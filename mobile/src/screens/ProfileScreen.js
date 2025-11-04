import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const BACKEND_URL = 'http://10.72.90.24:8000';

export default function ProfileScreen() {
  const router = useRouter();
  const [userReports, setUserReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userData, setUserData] = useState({
    name: 'Loading...',
    email: 'Loading...',
    userId: null
  });

  useEffect(() => {
    const fetchUserDataAndPosts = async () => {
      try {
        const auth = await import('@react-native-firebase/auth');
        const currentUser = auth.default().currentUser;

        if (currentUser) {
          setUserData({
            name: currentUser.displayName || 'User',
            email: currentUser.email || 'No email',
            userId: currentUser.uid
          });

          const response = await fetch(`${BACKEND_URL}/getUserPosts/${currentUser.uid}`);
          const data = await response.json();

          if (data.posts && Array.isArray(data.posts)) {
            const formattedPosts = data.posts.map(post => ({
              id: post.id,
              location_id: post.location_id,
              location: post.location_id,
              date: post.created_at,
              severity: calculateSeverity(post),
              description: post.text_descr || 'No description provided',
              surface_damage: post.surface_damage,
              traffic_safety_risk: post.traffic_safety_risk,
              ride_discomfort: post.ride_discomfort,
              waterlogging: post.waterlogging,
              urgency_for_repair: post.urgency_for_repair,
              images_dir: post.images_dir,
              images_count: post.images
            }));
            setUserReports(formattedPosts);
          } else {
            setUserReports([]);
          }
        }
      } catch (error) {
        console.error('Error fetching user posts:', error);
        Alert.alert('Error', 'Failed to load your reports');
      } finally {
        setLoading(false);
      }
    };

    fetchUserDataAndPosts();
  }, []);

  const calculateSeverity = (post) => {
    const avgScore = (
      post.surface_damage +
      post.traffic_safety_risk +
      post.ride_discomfort +
      post.waterlogging +
      post.urgency_for_repair
    ) / 5;

    if (avgScore >= 70) return 'High';
    if (avgScore >= 40) return 'Medium';
    return 'Low';
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'High':
        return '#ff4444';
      case 'Medium':
        return '#ffaa00';
      case 'Low':
        return '#00cc00';
      default:
        return '#666';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Resolved':
        return '#00cc00';
      case 'Reviewed':
        return '#ffaa00';
      case 'Pending':
        return '#ff4444';
      default:
        return '#666';
    }
  };

  if (selectedReport) {
    return (
      <View style={styles.container}>
        <View style={styles.detailHeader}>
          <TouchableOpacity
            style={styles.collapseButton}
            onPress={() => setSelectedReport(null)}
          >
            <Ionicons name="chevron-down" size={28} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.detailHeaderTitle}>Report Details</Text>
          <View style={styles.placeholder} />
        </View>

        <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
          <View style={styles.detailContainer}>
            <View style={styles.detailImageContainer}>
              {selectedReport.images_count > 0 ? (
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  {Array.from({ length: selectedReport.images_count }, (_, i) => {
                    const imgUrl = `${BACKEND_URL}/uploads/${selectedReport.images_dir}/${i}`;
                    return (
                      <Image
                        key={i}
                        source={{ uri: imgUrl }}
                        style={styles.detailImage}
                        onError={(e) => console.warn("Image load failed:", imgUrl)}
                      />
                    );
                  })}
                </ScrollView>
              ) : (
                <View style={styles.imagePlaceholder}>
                  <Ionicons name="image-outline" size={60} color="#999" />
                </View>
              )}
            </View>


            <View style={styles.detailContent}>
              <View style={styles.detailHeaderInfo}>
                <Text style={styles.detailReportId}>Report #{selectedReport.id}</Text>
              </View>

              <View style={styles.detailInfoBox}>
                <View style={styles.detailRow}>
                  <Ionicons name="location-outline" size={20} color="#000" />
                  <View style={styles.detailRowContent}>
                    <Text style={styles.detailRowLabel}>Location</Text>
                    <Text style={styles.detailRowValue}>{selectedReport.location}</Text>
                  </View>
                </View>
              </View>

              <View style={styles.detailInfoBox}>
                <View style={styles.detailRow}>
                  <Ionicons name="calendar-outline" size={20} color="#000" />
                  <View style={styles.detailRowContent}>
                    <Text style={styles.detailRowLabel}>Date Reported</Text>
                    <Text style={styles.detailRowValue}>{selectedReport.date}</Text>
                  </View>
                </View>
              </View>

              <View style={styles.detailInfoBox}>
                <View style={styles.detailRow}>
                  <Ionicons name="alert-circle-outline" size={20} color="#000" />
                  <View style={styles.detailRowContent}>
                    <Text style={styles.detailRowLabel}>Severity</Text>
                    <Text
                      style={[
                        styles.detailRowValue,
                        { color: getSeverityColor(selectedReport.severity) },
                      ]}
                    >
                      {selectedReport.severity}
                    </Text>
                  </View>
                </View>
              </View>

              <View style={styles.detailDescriptionBox}>
                <Text style={styles.detailDescriptionLabel}>Description</Text>
                <Text style={styles.detailDescriptionText}>
                  {selectedReport.description}
                </Text>
              </View>

              <TouchableOpacity
                style={styles.backToProfileButton}
                onPress={() => setSelectedReport(null)}
              >
                <Ionicons name="arrow-back" size={20} color="#fff" />
                <Text style={styles.backToProfileButtonText}>Back to Dashboard</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.bottomPadding} />
          </View>
        </ScrollView>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Profile</Text>
          <View style={styles.placeholder} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#000" />
          <Text style={styles.loadingText}>Loading your reports...</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Profile</Text>
        <View style={styles.placeholder} />
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.profileSection}>
          <View style={styles.avatarContainer}>
            <Ionicons name="person-circle-outline" size={100} color="#000" />
          </View>

          <View style={styles.userInfoContainer}>
            <Text style={styles.userName}>{userData.name}</Text>
            <Text style={styles.userEmail}>{userData.email}</Text>
          </View>

          <View style={styles.statsContainer}>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{userReports.length}</Text>
              <Text style={styles.statLabel}>Reports Made</Text>
            </View>
          </View>
        </View>

        <View style={styles.reportsSection}>
          <Text style={styles.sectionTitle}>Your Reports</Text>

          {userReports.length === 0 ? (
            <View style={styles.emptyStateContainer}>
              <Ionicons name="document-outline" size={60} color="#ccc" />
              <Text style={styles.emptyStateText}>No reports yet</Text>
              <Text style={styles.emptyStateSubtext}>Start contributing by reporting road conditions</Text>
            </View>
          ) : (
            userReports.map((report) => (
            <TouchableOpacity
              key={report.id}
              style={styles.reportCard}
              onPress={() => setSelectedReport(report)}
            >
              <View style={styles.reportHeader}>
                <Text style={styles.reportId}>Report #{report.id}</Text>
              </View>

              <View style={styles.reportBody}>
                <View style={styles.reportRow}>
                  <Ionicons name="location-outline" size={18} color="#666" />
                  <Text style={styles.reportLocation}>{report.location}</Text>
                </View>

                <View style={styles.reportRow}>
                  <Ionicons name="calendar-outline" size={18} color="#666" />
                  <Text style={styles.reportDate}>{report.date}</Text>
                </View>

                <View style={styles.reportRow}>
                  <Ionicons name="alert-circle-outline" size={18} color="#666" />
                  <Text style={styles.reportLabel}>Severity: </Text>
                  <Text
                    style={[
                      styles.reportSeverity,
                      { color: getSeverityColor(report.severity) },
                    ]}
                  >
                    {report.severity}
                  </Text>
                </View>
              </View>

              <View style={styles.viewDetailsButton}>
                <Text style={styles.viewDetailsText}>View Details</Text>
                <Ionicons name="chevron-forward" size={18} color="#000" />
              </View>
            </TouchableOpacity>
          ))
          )}
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 15,
    backgroundColor: '#000',
  },
  detailHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 15,
    backgroundColor: '#000',
  },
  backButton: {
    padding: 8,
  },
  collapseButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  detailHeaderTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  placeholder: {
    width: 40,
  },
  scrollView: {
    flex: 1,
  },
  profileSection: {
    alignItems: 'center',
    paddingVertical: 30,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  avatarContainer: {
    marginBottom: 20,
    borderWidth: 3,
    borderColor: '#000',
    borderRadius: 60,
    padding: 5,
  },
  userInfoContainer: {
    alignItems: 'center',
    marginBottom: 25,
  },
  userName: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 8,
  },
  userEmail: {
    fontSize: 16,
    color: '#666',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    width: '100%',
  },
  statBox: {
    alignItems: 'center',
    paddingHorizontal: 40,
    paddingVertical: 15,
    backgroundColor: '#f8f8f8',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#000',
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  reportsSection: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 20,
  },
  reportCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#000',
    padding: 16,
    marginBottom: 16,
  },
  reportHeader: {
    marginBottom: 12,
  },
  reportId: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
  },
  reportBody: {
    marginBottom: 12,
  },
  reportRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  reportLocation: {
    fontSize: 14,
    color: '#333',
    marginLeft: 8,
    flex: 1,
  },
  reportDate: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
  },
  reportLabel: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
  },
  reportSeverity: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  viewDetailsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#000',
  },
  viewDetailsText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    marginRight: 5,
  },
  detailContainer: {
    padding: 20,
  },
  detailImageContainer: {
    marginBottom: 25,
  },
  imagePlaceholder: {
    width: '100%',
    height: 250,
    backgroundColor: '#f0f0f0',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  detailContent: {
    width: '100%',
  },
  detailHeaderInfo: {
    marginBottom: 20,
  },
  detailReportId: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
  },
  detailInfoBox: {
    marginBottom: 16,
    backgroundColor: '#f8f8f8',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    padding: 16,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  detailRowContent: {
    marginLeft: 12,
    flex: 1,
  },
  detailRowLabel: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
    marginBottom: 4,
  },
  detailRowValue: {
    fontSize: 16,
    color: '#000',
    fontWeight: '500',
  },
  detailDescriptionBox: {
    marginBottom: 20,
    backgroundColor: '#f8f8f8',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    padding: 16,
  },
  detailDescriptionLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 10,
  },
  detailDescriptionText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  backToProfileButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    backgroundColor: '#000',
    borderRadius: 8,
    marginBottom: 20,
  },
  backToProfileButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginLeft: 8,
  },
  bottomPadding: {
    height: 30,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#666',
  },
  emptyStateContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 15,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  detailImage: {
  width: 200,
  height: 200,
  borderRadius: 12,
  borderWidth: 2,
  borderColor: '#000',
  marginRight: 10,
},
});