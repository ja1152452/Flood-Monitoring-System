import { query, withTransaction } from '../../config/db.js';
import { ApiError } from '../../utils/ApiError.js';
import { parsePagination, paginate } from '../../utils/pagination.js';

export const ingestReading = async (cameraId, dto) => {
  return withTransaction(async (client) => {

    let camId = cameraId;
    if (!camId && dto.camera_code) {
      const { rows: cam } = await client.query(
        `SELECT id FROM cameras WHERE camera_code = $1`,
        [dto.camera_code]
      );
      if (!cam.length) throw new Error('Camera not found');
      camId = cam[0].id;
    }

    const { rows } = await client.query(
      `INSERT INTO water_level_readings
         (camera_id, water_level_m, flood_level, waterline_pixel_y, confidence, captured_at)
       VALUES ($1,$2,$3,$4,$5,$6)
       RETURNING *`,
      [
        camId,
        dto.water_level_m,
        dto.flood_level,
        dto.waterline_pixel_y || null,
        dto.confidence        || null,
        dto.captured_at       || new Date().toISOString(),
      ]
    );

    await client.query(
      'UPDATE cameras SET last_heartbeat_at = NOW() WHERE id = $1',
      [camId]
    );

    const reading = rows[0];

    const { evaluateAndDispatch } = await import('../alerts/alerts.service.js');
    await evaluateAndDispatch(reading, client);

    return reading;
  });
};

export const getLatest = async (cameraId) => {
  const { rows } = await query(
    `SELECT r.*,
            c.location_name,
            b.name AS barangay
     FROM water_level_readings r
     JOIN cameras c ON c.id = r.camera_id
     LEFT JOIN barangays b ON b.id = c.barangay_id
     WHERE r.camera_id = $1
     ORDER BY r.captured_at DESC
     LIMIT 1`,
    [cameraId]
  );
  if (!rows.length) return null;
  return rows[0];
};

export const getHistory = async (cameraId, queryParams) => {
  const { page, limit, offset } = parsePagination(queryParams);
  const { from, to, date, flood_level } = queryParams;
  const conditions = ['camera_id = $1'];
  const params     = [cameraId];
  let i = 2;
  if (date) {
    conditions.push(`captured_at >= $${i++}`); params.push(`${date}T00:00:00+08:00`);
    conditions.push(`captured_at <= $${i++}`); params.push(`${date}T23:59:59+08:00`);
  } else {
    if (from) { conditions.push(`captured_at >= $${i++}`); params.push(from); }
    if (to)   { conditions.push(`captured_at <= $${i++}`); params.push(to); }
  }
  if (flood_level) { conditions.push(`flood_level = $${i++}`); params.push(flood_level); }
  const where = conditions.join(' AND ');

  const [{ rows: data }, { rows: count }] = await Promise.all([
    query(
      `SELECT id, water_level_m, flood_level, confidence, captured_at
       FROM water_level_readings WHERE ${where}
       ORDER BY captured_at DESC LIMIT $${i} OFFSET $${i + 1}`,
      [...params, limit, offset]
    ),
    query(`SELECT COUNT(*) FROM water_level_readings WHERE ${where}`, params),
  ]);

  return paginate(data, parseInt(count[0].count), { page, limit });
};

export const getTrend = async (cameraId, minutes = 30) => {
  const { rows } = await query(
    `SELECT water_level_m, captured_at
     FROM water_level_readings
     WHERE camera_id = $1 AND captured_at >= NOW() - ($2 || ' minutes')::interval
     ORDER BY captured_at DESC
     LIMIT 10`,
    [cameraId, minutes]
  );

  if (rows.length < 2) return { trend: 'STABLE', delta_m: 0 };

  const latest   = parseFloat(rows[0].water_level_m);
  const previous = parseFloat(rows[rows.length - 1].water_level_m);
  const delta    = latest - previous;

  return {
    trend:   delta > 0.05 ? 'RISING' : delta < -0.05 ? 'FALLING' : 'STABLE',
    delta_m: parseFloat(delta.toFixed(4)),
    latest_m: latest,
  };
};