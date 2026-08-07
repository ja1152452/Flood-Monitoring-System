import { useEffect } from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet, ScrollView, Vibration } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const LEVEL_CONFIG = {
  MONITOR:    { icon: 'information-circle', color: '#f59e0b', bg: '#451a03', label: 'Monitor Level',    hours: 6    },
  ALERT:      { icon: 'notifications',      color: '#f97316', bg: '#431407', label: 'Alert Level',      hours: 3    },
  EVACUATION: { icon: 'warning',            color: '#ef4444', bg: '#450a0a', label: 'Evacuation Level', hours: 1    },
  CRITICAL:   { icon: 'alert-circle',       color: '#7c3aed', bg: '#2e1065', label: 'Critical Level',   hours: null },
};

export function FloodAlertModal({ visible, level, centers = [], onDismiss }) {
  const cfg = LEVEL_CONFIG[level] || LEVEL_CONFIG.MONITOR;
  const IconComponent = cfg.icon;

  const timeText = cfg.hours
    ? `Rising flood waters are expected in the next ${cfg.hours} hour${cfg.hours > 1 ? 's' : ''}.`
    : 'Critical condition. Please evacuate to the nearest center immediately.';

  useEffect(() => {
    if (visible) {
      Vibration.vibrate(1000);
    } else {
      Vibration.cancel();
    }
  }, [visible]);

  if (!visible || !level) return null;

  return (
    <Modal
      visible={visible}
      transparent={false}
      animationType="fade"
      statusBarTranslucent
      onRequestClose={onDismiss}>
      <View style={[styles.screen, { backgroundColor: '#0f172a' }]}>
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}>

          <View style={[styles.iconRow, { backgroundColor: cfg.bg }]}>
            <Ionicons name={cfg.icon} size={40} color={cfg.color} />
          </View>

          <View style={[styles.badge, { backgroundColor: cfg.color + '22', borderColor: cfg.color }]}>
            <Text style={[styles.badgeText, { color: cfg.color }]}>{cfg.label.toUpperCase()}</Text>
          </View>

          <Text style={[styles.title, { color: cfg.color }]}>
            Water level has reached {cfg.label}.
          </Text>

          <Text style={styles.message}>
            {timeText} {cfg.hours ? 'Please prepare for possible evacuation.' : ''}
          </Text>

          <View style={[styles.centersBox, { borderColor: cfg.color + '44' }]}>
            <Text style={[styles.centersTitle, { color: cfg.color }]}>
              Available Evacuation Centers:
            </Text>
            {centers.length > 0 ? centers.map((c, i) => (
              <View key={i} style={styles.centerItemContainer}>
                <View style={[styles.bullet, { backgroundColor: cfg.color }]} />
                <Text style={styles.centerItem}>
                  {c.name} <Text style={{ color: '#94a3b8' }}>({c.available_slots} slots)</Text>
                </Text>
              </View>
            )) : (
              <Text style={styles.centerItem}>
                No available centers in your barangay.
              </Text>
            )}
          </View>

          <Text style={styles.author}>Issued by: MDRRMO Lumban</Text>

          <TouchableOpacity
            style={[styles.dismissBtn, { backgroundColor: cfg.color }]}
            onPress={onDismiss}
            activeOpacity={0.8}>
            <Text style={styles.dismissText}>I Understand</Text>
          </TouchableOpacity>

        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  content: {
    flexGrow:          1,
    justifyContent:    'center',
    alignItems:        'center',
    paddingHorizontal: 24,
    paddingVertical:   60,
    gap:               16,
  },
  iconRow: {
    width:          90,
    height:         90,
    borderRadius:   45,
    justifyContent: 'center',
    alignItems:     'center',
    marginBottom:   8,
  },
  badge: {
    borderWidth:       1,
    borderRadius:      20,
    paddingHorizontal: 16,
    paddingVertical:   6,
  },
  badgeText:    { fontSize: 13, fontWeight: '800', letterSpacing: 1.5 },
  title:        { fontSize: 24, fontWeight: '800', textAlign: 'center', lineHeight: 32 },
  message:      { fontSize: 16, color: '#e2e8f0', textAlign: 'center', lineHeight: 24, paddingHorizontal: 10 },
  centersBox: {
    width:           '100%',
    borderWidth:     1,
    borderRadius:    16,
    padding:         20,
    backgroundColor: '#1e293b',
    gap:             10,
    marginTop:       10,
  },
  centersTitle: { fontSize: 14, fontWeight: '700', marginBottom: 8, letterSpacing: 0.5 },
  centerItemContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  bullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  centerItem:   { fontSize: 15, color: '#f8fafc', lineHeight: 22 },
  author:       { fontSize: 13, color: '#94a3b8', marginTop: 10 },
  dismissBtn: {
    width:           '100%',
    paddingVertical: 16,
    borderRadius:    14,
    alignItems:      'center',
    marginTop:       20,
    shadowColor:     '#000',
    shadowOffset:    { width: 0, height: 4 },
    shadowOpacity:   0.3,
    shadowRadius:    6,
    elevation:       8,
  },
  dismissText: { fontSize: 17, fontWeight: '800', color: '#fff', letterSpacing: 0.5 },
});
