import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Header, 
  SpaceBetween, 
  Box, 
  ColumnLayout,
  Cards,
  CardsProps,
  Table,
  TableProps,
  Pagination,
  Button,
  StatusIndicator,
  Modal,
  FormField,
  Textarea,
  Select,
  SelectProps,
  Alert,
  Link,
  Grid
} from '@cloudscape-design/components';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import axios from 'axios';

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Match status options
const STATUS_OPTIONS = [
  { label: 'Scheduled', value: 'scheduled' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' },
  { label: 'Missed', value: 'missed' }
];

// Match feedback rating options
const RATING_OPTIONS = [
  { label: '5 - Excellent', value: '5' },
  { label: '4 - Good', value: '4' },
  { label: '3 - Average', value: '3' },
  { label: '2 - Below Average', value: '2' },
  { label: '1 - Poor', value: '1' }
];

// Match interface
interface Match {
  id: string;
  participants: {
    id: string;
    name: string;
    email: string;
  }[];
  scheduled_date: string;
  status: string;
  created_at: string;
  feedback?: {
    rating: number;
    comments: string;
  };
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  
  // Current match state
  const [currentMatch, setCurrentMatch] = useState<Match | null>(null);
  const [isLoadingCurrent, setIsLoadingCurrent] = useState(true);
  
  // Match history state
  const [matchHistory, setMatchHistory] = useState<Match[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedItems, setSelectedItems] = useState<Match[]>([]);
  
  // Feedback modal state
  const [isFeedbackModalVisible, setIsFeedbackModalVisible] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<SelectProps.Option | null>(null);
  const [feedbackComments, setFeedbackComments] = useState('');
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  
  // Status update modal state
  const [isStatusModalVisible, setIsStatusModalVisible] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<SelectProps.Option | null>(null);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  
  // Load current match
  useEffect(() => {
    const fetchCurrentMatch = async () => {
      try {
        setIsLoadingCurrent(true);
        const response = await axios.get(`${API_URL}/matches/current`, {
          withCredentials: true
        });
        
        if (response.data) {
          setCurrentMatch(response.data);
        } else {
          setCurrentMatch(null);
        }
      } catch (err) {
        console.error('Error fetching current match:', err);
        setCurrentMatch(null);
      } finally {
        setIsLoadingCurrent(false);
      }
    };
    
    fetchCurrentMatch();
  }, []);
  
  // Load match history
  useEffect(() => {
    const fetchMatchHistory = async () => {
      try {
        setIsLoadingHistory(true);
        const response = await axios.get(`${API_URL}/matches/history`, {
          params: { page: currentPage, limit: 10 },
          withCredentials: true
        });
        
        setMatchHistory(response.data.matches || []);
        setTotalPages(response.data.total_pages || 1);
      } catch (err) {
        console.error('Error fetching match history:', err);
        setMatchHistory([]);
        setTotalPages(1);
      } finally {
        setIsLoadingHistory(false);
      }
    };
    
    fetchMatchHistory();
  }, [currentPage]);
  
  // Handle feedback submission
  const handleFeedbackSubmit = async () => {
    if (!selectedMatch || !feedbackRating) return;
    
    try {
      setIsSubmittingFeedback(true);
      
      await axios.post(`${API_URL}/matches/feedback`, {
        match_id: selectedMatch.id,
        rating: parseInt(feedbackRating.value as string),
        comments: feedbackComments
      }, {
        withCredentials: true
      });
      
      // Update match in state
      const updatedMatch = {
        ...selectedMatch,
        feedback: {
          rating: parseInt(feedbackRating.value as string),
          comments: feedbackComments
        }
      };
      
      if (currentMatch?.id === selectedMatch.id) {
        setCurrentMatch(updatedMatch);
      }
      
      setMatchHistory(prev => 
        prev.map(match => match.id === selectedMatch.id ? updatedMatch : match)
      );
      
      // Show success notification
      addNotification({
        type: 'success',
        content: 'Feedback submitted successfully',
        dismissible: true,
        onDismiss: () => {}
      });
      
      // Close modal and reset state
      setIsFeedbackModalVisible(false);
      setSelectedMatch(null);
      setFeedbackRating(null);
      setFeedbackComments('');
    } catch (err) {
      // Show error notification
      addNotification({
        type: 'error',
        content: 'Failed to submit feedback',
        dismissible: true,
        onDismiss: () => {}
      });
      console.error('Feedback submission error:', err);
    } finally {
      setIsSubmittingFeedback(false);
    }
  };
  
  // Handle status update
  const handleStatusUpdate = async () => {
    if (!selectedMatch || !selectedStatus) return;
    
    try {
      setIsUpdatingStatus(true);
      
      await axios.put(`${API_URL}/matches/${selectedMatch.id}/status`, {
        status: selectedStatus.value
      }, {
        withCredentials: true
      });
      
      // Update match in state
      const updatedMatch = {
        ...selectedMatch,
        status: selectedStatus.value as string
      };
      
      if (currentMatch?.id === selectedMatch.id) {
        setCurrentMatch(updatedMatch);
      }
      
      setMatchHistory(prev => 
        prev.map(match => match.id === selectedMatch.id ? updatedMatch : match)
      );
      
      // Show success notification
      addNotification({
        type: 'success',
        content: 'Match status updated successfully',
        dismissible: true,
        onDismiss: () => {}
      });
      
      // Close modal and reset state
      setIsStatusModalVisible(false);
      setSelectedMatch(null);
      setSelectedStatus(null);
    } catch (err) {
      // Show error notification
      addNotification({
        type: 'error',
        content: 'Failed to update match status',
        dismissible: true,
        onDismiss: () => {}
      });
      console.error('Status update error:', err);
    } finally {
      setIsUpdatingStatus(false);
    }
  };
  
  // Open feedback modal
  const openFeedbackModal = (match: Match) => {
    setSelectedMatch(match);
    
    if (match.feedback) {
      setFeedbackRating(RATING_OPTIONS.find(option => 
        parseInt(option.value as string) === match.feedback?.rating
      ) || null);
      setFeedbackComments(match.feedback.comments || '');
    } else {
      setFeedbackRating(null);
      setFeedbackComments('');
    }
    
    setIsFeedbackModalVisible(true);
  };
  
  // Open status modal
  const openStatusModal = (match: Match) => {
    setSelectedMatch(match);
    setSelectedStatus(STATUS_OPTIONS.find(option => option.value === match.status) || null);
    setIsStatusModalVisible(true);
  };
  
  // Get status indicator
  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'scheduled':
        return <StatusIndicator type="pending">Scheduled</StatusIndicator>;
      case 'completed':
        return <StatusIndicator type="success">Completed</StatusIndicator>;
      case 'cancelled':
        return <StatusIndicator type="stopped">Cancelled</StatusIndicator>;
      case 'missed':
        return <StatusIndicator type="error">Missed</StatusIndicator>;
      default:
        return <StatusIndicator type="info">{status}</StatusIndicator>;
    }
  };
  
  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };
  
  // Card definition for current match
  const cardDefinition: CardsProps.CardDefinition<Match> = {
    header: item => (
      <div>
        <Link onFollow={() => openStatusModal(item)}>
          Match on {formatDate(item.scheduled_date)}
        </Link>
      </div>
    ),
    sections: [
      {
        id: 'participants',
        header: 'Participants',
        content: item => (
          <div>
            {item.participants
              .filter(p => p.id !== user?.id)
              .map((participant, index) => (
                <div key={participant.id}>
                  <strong>{participant.name}</strong><br />
                  <span>{participant.email}</span>
                  {index < item.participants.length - 2 && <hr />}
                </div>
              ))}
          </div>
        )
      },
      {
        id: 'status',
        header: 'Status',
        content: item => getStatusIndicator(item.status)
      },
      {
        id: 'actions',
        header: 'Actions',
        content: item => (
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={() => openStatusModal(item)}>Update status</Button>
            <Button onClick={() => openFeedbackModal(item)}>
              {item.feedback ? 'Edit feedback' : 'Add feedback'}
            </Button>
          </SpaceBetween>
        )
      }
    ]
  };
  
  // Column definitions for match history table
  const columnDefinitions: TableProps.ColumnDefinition<Match>[] = [
    {
      id: 'date',
      header: 'Date',
      cell: item => formatDate(item.scheduled_date),
      sortingField: 'scheduled_date'
    },
    {
      id: 'participants',
      header: 'Participants',
      cell: item => item.participants
        .filter(p => p.id !== user?.id)
        .map(p => p.name)
        .join(', ')
    },
    {
      id: 'status',
      header: 'Status',
      cell: item => getStatusIndicator(item.status)
    },
    {
      id: 'feedback',
      header: 'Feedback',
      cell: item => item.feedback 
        ? `${item.feedback.rating}/5` 
        : <StatusIndicator type="pending">Not provided</StatusIndicator>
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: item => (
        <SpaceBetween direction="horizontal" size="xs">
          <Button onClick={() => openStatusModal(item)}>Update status</Button>
          <Button onClick={() => openFeedbackModal(item)}>
            {item.feedback ? 'Edit feedback' : 'Add feedback'}
          </Button>
        </SpaceBetween>
      )
    }
  ];
  
  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header
            variant="h2"
            description="Welcome to your Virtual Coffee Platform dashboard"
          >
            Hello, {user?.name}!
          </Header>
        }
      >
        <Grid
          gridDefinition={[
            { colspan: { default: 12, xxs: 12, xs: 6 } },
            { colspan: { default: 12, xxs: 12, xs: 6 } }
          ]}
        >
          <div>
            <Box variant="awsui-key-label">Status</Box>
            <div>
              {user?.is_paused ? (
                <StatusIndicator type="stopped">Paused</StatusIndicator>
              ) : (
                <StatusIndicator type="success">Active</StatusIndicator>
              )}
            </div>
          </div>
          <div>
            <Box variant="awsui-key-label">Next Match</Box>
            <div>
              {isLoadingCurrent ? (
                'Loading...'
              ) : currentMatch ? (
                formatDate(currentMatch.scheduled_date)
              ) : (
                'No upcoming matches'
              )}
            </div>
          </div>
        </Grid>
      </Container>
      
      <Container
        header={
          <Header
            variant="h2"
            description="Your current coffee match"
            actions={
              <Button
                onClick={() => {
                  // Refresh current match
                  setIsLoadingCurrent(true);
                  axios.get(`${API_URL}/matches/current`, {
                    withCredentials: true
                  })
                    .then(response => {
                      setCurrentMatch(response.data);
                    })
                    .catch(err => {
                      console.error('Error refreshing current match:', err);
                    })
                    .finally(() => {
                      setIsLoadingCurrent(false);
                    });
                }}
              >
                Refresh
              </Button>
            }
          >
            Current Match
          </Header>
        }
      >
        {isLoadingCurrent ? (
          <Box textAlign="center">Loading current match...</Box>
        ) : currentMatch ? (
          <Cards
            items={[currentMatch]}
            cardDefinition={cardDefinition}
            cardsPerRow={[
              { cards: 1 }
            ]}
            empty={
              <Box textAlign="center" color="inherit">
                <b>No current match</b>
                <Box padding={{ bottom: "s" }} variant="p" color="inherit">
                  You don't have any active coffee matches at the moment.
                </Box>
              </Box>
            }
          />
        ) : (
          <Box textAlign="center">
            <b>No current match</b>
            <Box padding={{ bottom: "s" }} variant="p">
              {user?.is_paused ? (
                <Alert
                  type="info"
                  header="Participation paused"
                >
                  You are currently not participating in coffee meetings. Visit your profile to resume participation.
                </Alert>
              ) : (
                "You don't have any active coffee matches at the moment."
              )}
            </Box>
          </Box>
        )}
      </Container>
      
      <Container
        header={
          <Header
            variant="h2"
            description="Your past coffee matches"
            actions={
              <Button
                onClick={() => {
                  // Refresh match history
                  setIsLoadingHistory(true);
                  axios.get(`${API_URL}/matches/history`, {
                    params: { page: currentPage, limit: 10 },
                    withCredentials: true
                  })
                    .then(response => {
                      setMatchHistory(response.data.matches || []);
                      setTotalPages(response.data.total_pages || 1);
                    })
                    .catch(err => {
                      console.error('Error refreshing match history:', err);
                    })
                    .finally(() => {
                      setIsLoadingHistory(false);
                    });
                }}
              >
                Refresh
              </Button>
            }
          >
            Match History
          </Header>
        }
      >
        <Table
          items={matchHistory}
          columnDefinitions={columnDefinitions}
          loading={isLoadingHistory}
          loadingText="Loading match history"
          selectionType="single"
          selectedItems={selectedItems}
          onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}
          empty={
            <Box textAlign="center" color="inherit">
              <b>No match history</b>
              <Box padding={{ bottom: "s" }} variant="p" color="inherit">
                You don't have any past coffee matches.
              </Box>
            </Box>
          }
          pagination={
            <Pagination
              currentPageIndex={currentPage}
              pagesCount={totalPages}
              onChange={({ detail }) => setCurrentPage(detail.currentPageIndex)}
            />
          }
        />
      </Container>
      
      {/* Feedback Modal */}
      <Modal
        visible={isFeedbackModalVisible}
        onDismiss={() => setIsFeedbackModalVisible(false)}
        header="Match Feedback"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={() => setIsFeedbackModalVisible(false)}>Cancel</Button>
              <Button
                variant="primary"
                onClick={handleFeedbackSubmit}
                loading={isSubmittingFeedback}
                disabled={!feedbackRating}
              >
                Submit feedback
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="l">
          {selectedMatch && (
            <Box variant="p">
              Provide feedback for your coffee match on {formatDate(selectedMatch.scheduled_date)}
              with {selectedMatch.participants.filter(p => p.id !== user?.id).map(p => p.name).join(', ')}.
            </Box>
          )}
          
          <FormField
            label="Rating"
            description="How would you rate this coffee meeting?"
          >
            <Select
              selectedOption={feedbackRating}
              onChange={({ detail }) => setFeedbackRating(detail.selectedOption)}
              options={RATING_OPTIONS}
              placeholder="Select a rating"
            />
          </FormField>
          
          <FormField
            label="Comments"
            description="Share your thoughts about this coffee meeting"
          >
            <Textarea
              value={feedbackComments}
              onChange={({ detail }) => setFeedbackComments(detail.value)}
              placeholder="Optional comments"
            />
          </FormField>
        </SpaceBetween>
      </Modal>
      
      {/* Status Update Modal */}
      <Modal
        visible={isStatusModalVisible}
        onDismiss={() => setIsStatusModalVisible(false)}
        header="Update Match Status"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={() => setIsStatusModalVisible(false)}>Cancel</Button>
              <Button
                variant="primary"
                onClick={handleStatusUpdate}
                loading={isUpdatingStatus}
                disabled={!selectedStatus || (selectedMatch && selectedMatch.status === selectedStatus?.value)}
              >
                Update status
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="l">
          {selectedMatch && (
            <Box variant="p">
              Update the status of your coffee match on {formatDate(selectedMatch.scheduled_date)}
              with {selectedMatch.participants.filter(p => p.id !== user?.id).map(p => p.name).join(', ')}.
            </Box>
          )}
          
          <FormField
            label="Status"
            description="Select the current status of this coffee meeting"
          >
            <Select
              selectedOption={selectedStatus}
              onChange={({ detail }) => setSelectedStatus(detail.selectedOption)}
              options={STATUS_OPTIONS}
              placeholder="Select a status"
            />
          </FormField>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  );
};

export default Dashboard;