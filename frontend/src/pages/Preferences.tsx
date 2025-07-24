import React, { useState, useEffect } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  Alert,
  Form,
  FormField,
  Multiselect,
  MultiselectProps,
  Select,
  SelectProps,
  Tabs,
  Toggle,
  Input,
  Button,
  ColumnLayout
} from '@cloudscape-design/components';
import { useAuth } from '../contexts/AuthContext.js';
import { useNotifications } from '../contexts/NotificationContext.js';
import axios from 'axios';

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Topic options
const TOPIC_OPTIONS = [
  { label: 'Work-related', value: 'work' },
  { label: 'Technology', value: 'tech' },
  { label: 'Career development', value: 'career' },
  { label: 'Hobbies', value: 'hobbies' },
  { label: 'Sports', value: 'sports' },
  { label: 'Movies & TV', value: 'entertainment' },
  { label: 'Books', value: 'books' },
  { label: 'Travel', value: 'travel' },
  { label: 'Food & Cooking', value: 'food' },
  { label: 'Music', value: 'music' },
  { label: 'Gaming', value: 'gaming' },
  { label: 'Pets', value: 'pets' }
];

// Availability options
const AVAILABILITY_OPTIONS = [
  { label: 'Monday morning', value: 'mon-am' },
  { label: 'Monday afternoon', value: 'mon-pm' },
  { label: 'Tuesday morning', value: 'tue-am' },
  { label: 'Tuesday afternoon', value: 'tue-pm' },
  { label: 'Wednesday morning', value: 'wed-am' },
  { label: 'Wednesday afternoon', value: 'wed-pm' },
  { label: 'Thursday morning', value: 'thu-am' },
  { label: 'Thursday afternoon', value: 'thu-pm' },
  { label: 'Friday morning', value: 'fri-am' },
  { label: 'Friday afternoon', value: 'fri-pm' }
];

// Meeting length options
const MEETING_LENGTH_OPTIONS = [
  { label: '15 minutes', value: '15' },
  { label: '30 minutes', value: '30' },
  { label: '45 minutes', value: '45' },
  { label: '60 minutes', value: '60' }
];

const Preferences: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const { addNotification } = useNotifications();
  const [activeTabId, setActiveTabId] = useState('meeting');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Meeting preferences
  const [selectedTopics, setSelectedTopics] = useState<MultiselectProps.Option[]>([]);
  const [selectedAvailability, setSelectedAvailability] = useState<MultiselectProps.Option[]>([]);
  const [selectedMeetingLength, setSelectedMeetingLength] = useState<SelectProps.Option | null>(null);

  // Notification preferences
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [slackEnabled, setSlackEnabled] = useState(false);
  const [slackWebhook, setSlackWebhook] = useState('');
  const [telegramEnabled, setTelegramEnabled] = useState(false);
  const [telegramChatId, setTelegramChatId] = useState('');
  const [signalEnabled, setSignalEnabled] = useState(false);
  const [signalNumber, setSignalNumber] = useState('');
  const [primaryChannel, setPrimaryChannel] = useState<SelectProps.Option | null>(null);

  // Initialize form values from user data
  useEffect(() => {
    if (user?.preferences) {
      // Set topics
      const topics = user.preferences.topics.map(topic => {
        const option = TOPIC_OPTIONS.find(opt => opt.value === topic);
        return option || { label: topic, value: topic };
      });
      setSelectedTopics(topics);

      // Set availability
      const availability = user.preferences.availability.map(avail => {
        const option = AVAILABILITY_OPTIONS.find(opt => opt.value === avail);
        return option || { label: avail, value: avail };
      });
      setSelectedAvailability(availability);

      // Set meeting length
      const meetingLength = MEETING_LENGTH_OPTIONS.find(
        opt => opt.value === user.preferences.meeting_length.toString()
      );
      setSelectedMeetingLength(meetingLength || null);
    }

    if (user?.notification_prefs) {
      setEmailEnabled(user.notification_prefs.email);
      setSlackEnabled(user.notification_prefs.slack);
      setSlackWebhook(user.notification_prefs.slack_webhook || '');
      setTelegramEnabled(user.notification_prefs.telegram);
      setTelegramChatId(user.notification_prefs.telegram_chat_id || '');
      setSignalEnabled(user.notification_prefs.signal);
      setSignalNumber(user.notification_prefs.signal_number || '');

      // Set primary channel
      const primaryChannelOption = [
        { label: 'Email', value: 'email' },
        { label: 'Slack', value: 'slack' },
        { label: 'Telegram', value: 'telegram' },
        { label: 'Signal', value: 'signal' }
      ].find(opt => opt.value === user.notification_prefs.primary_channel);

      setPrimaryChannel(primaryChannelOption || { label: 'Email', value: 'email' });
    }
  }, [user]);

  // Handle meeting preferences submission
  const handleMeetingPreferencesSubmit = async () => {
    try {
      setIsSubmitting(true);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Refresh user data
      await refreshUser();

      // Show success notification
      addNotification({
        type: 'success',
        content: 'Meeting preferences updated successfully',
        dismissible: true,
        onDismiss: () => {}
      });
    } catch (err) {
      // Show error notification
      addNotification({
        type: 'error',
        content: 'Failed to update meeting preferences',
        dismissible: true,
        onDismiss: () => {}
      });
      console.error('Preferences update error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle notification preferences submission
  const handleNotificationPreferencesSubmit = async () => {
    try {
      setIsSubmitting(true);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Refresh user data
      await refreshUser();

      // Show success notification
      addNotification({
        type: 'success',
        content: 'Notification preferences updated successfully',
        dismissible: true,
        onDismiss: () => {}
      });
    } catch (err) {
      // Show error notification
      addNotification({
        type: 'error',
        content: 'Failed to update notification preferences',
        dismissible: true,
        onDismiss: () => {}
      });
      console.error('Notification preferences update error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Configure your coffee meeting preferences"
        >
          Preferences
        </Header>
      }
    >
      <SpaceBetween size="l">
        <Tabs
          activeTabId={activeTabId}
          onChange={({ detail }) => setActiveTabId(detail.activeTabId)}
          tabs={[
            {
              id: 'meeting',
              label: 'Meeting preferences',
              content: (
                <Form
                  actions={
                    <Button
                      variant="primary"
                      onClick={handleMeetingPreferencesSubmit}
                      loading={isSubmitting && activeTabId === 'meeting'}
                    >
                      Save changes
                    </Button>
                  }
                >
                  <SpaceBetween size="l">
                    <FormField
                      label="Topics of interest"
                      description="Select topics you'd like to discuss during coffee meetings"
                    >
                      <Multiselect
                        selectedOptions={selectedTopics}
                        onChange={({ detail }) => setSelectedTopics(detail.selectedOptions)}
                        options={TOPIC_OPTIONS}
                        placeholder="Select topics"
                        filteringType="auto"
                        deselectAriaLabel={option => `Remove ${option.label}`}
                      />
                    </FormField>

                    <FormField
                      label="Availability"
                      description="Select times when you're available for coffee meetings"
                    >
                      <Multiselect
                        selectedOptions={selectedAvailability}
                        onChange={({ detail }) => setSelectedAvailability(detail.selectedOptions)}
                        options={AVAILABILITY_OPTIONS}
                        placeholder="Select availability"
                        filteringType="auto"
                        deselectAriaLabel={option => `Remove ${option.label}`}
                      />
                    </FormField>

                    <FormField
                      label="Preferred meeting length"
                      description="Select your preferred meeting duration"
                    >
                      <Select
                        selectedOption={selectedMeetingLength}
                        onChange={({ detail }) => setSelectedMeetingLength(detail.selectedOption)}
                        options={MEETING_LENGTH_OPTIONS}
                        placeholder="Select meeting length"
                      />
                    </FormField>
                  </SpaceBetween>
                </Form>
              )
            },
            {
              id: 'notification',
              label: 'Notification preferences',
              content: (
                <Form
                  actions={
                    <Button
                      variant="primary"
                      onClick={handleNotificationPreferencesSubmit}
                      loading={isSubmitting && activeTabId === 'notification'}
                    >
                      Save changes
                    </Button>
                  }
                >
                  <SpaceBetween size="l">
                    <Alert
                      type="info"
                      header="Multiple notification channels"
                    >
                      You can enable multiple notification channels. Your primary channel will be used first, with others as fallbacks.
                    </Alert>

                    <FormField
                      label="Primary notification channel"
                      description="Select your preferred notification method"
                    >
                      <Select
                        selectedOption={primaryChannel}
                        onChange={({ detail }) => setPrimaryChannel(detail.selectedOption)}
                        options={[
                          { label: 'Email', value: 'email' },
                          { label: 'Slack', value: 'slack', disabled: !slackEnabled },
                          { label: 'Telegram', value: 'telegram', disabled: !telegramEnabled },
                          { label: 'Signal', value: 'signal', disabled: !signalEnabled }
                        ]}
                        placeholder="Select primary channel"
                      />
                    </FormField>

                    <ColumnLayout columns={1}>
                      <FormField
                        label="Email notifications"
                        description="Receive match notifications via email"
                      >
                        <Toggle
                          checked={emailEnabled}
                          onChange={({ detail }) => setEmailEnabled(detail.checked)}
                        >
                          {emailEnabled ? 'Enabled' : 'Disabled'}
                        </Toggle>
                      </FormField>

                      <SpaceBetween size="l">
                        <FormField
                          label="Slack notifications"
                          description="Receive match notifications via Slack"
                        >
                          <Toggle
                            checked={slackEnabled}
                            onChange={({ detail }) => {
                              setSlackEnabled(detail.checked);
                              if (!detail.checked && primaryChannel?.value === 'slack') {
                                setPrimaryChannel({ label: 'Email', value: 'email' });
                              }
                            }}
                          >
                            {slackEnabled ? 'Enabled' : 'Disabled'}
                          </Toggle>
                        </FormField>

                        {slackEnabled && (
                          <FormField
                            label="Slack webhook URL"
                            description="Enter your Slack webhook URL to receive notifications"
                          >
                            <Input
                              value={slackWebhook}
                              onChange={({ detail }) => setSlackWebhook(detail.value)}
                              placeholder="https://hooks.slack.com/services/..."
                            />
                          </FormField>
                        )}
                      </SpaceBetween>

                      <SpaceBetween size="l">
                        <FormField
                          label="Telegram notifications"
                          description="Receive match notifications via Telegram"
                        >
                          <Toggle
                            checked={telegramEnabled}
                            onChange={({ detail }) => {
                              setTelegramEnabled(detail.checked);
                              if (!detail.checked && primaryChannel?.value === 'telegram') {
                                setPrimaryChannel({ label: 'Email', value: 'email' });
                              }
                            }}
                          >
                            {telegramEnabled ? 'Enabled' : 'Disabled'}
                          </Toggle>
                        </FormField>

                        {telegramEnabled && (
                          <FormField
                            label="Telegram chat ID"
                            description="Enter your Telegram chat ID to receive notifications"
                          >
                            <Input
                              value={telegramChatId}
                              onChange={({ detail }) => setTelegramChatId(detail.value)}
                            />
                          </FormField>
                        )}
                      </SpaceBetween>

                      <SpaceBetween size="l">
                        <FormField
                          label="Signal notifications"
                          description="Receive match notifications via Signal"
                        >
                          <Toggle
                            checked={signalEnabled}
                            onChange={({ detail }) => {
                              setSignalEnabled(detail.checked);
                              if (!detail.checked && primaryChannel?.value === 'signal') {
                                setPrimaryChannel({ label: 'Email', value: 'email' });
                              }
                            }}
                          >
                            {signalEnabled ? 'Enabled' : 'Disabled'}
                          </Toggle>
                        </FormField>

                        {signalEnabled && (
                          <FormField
                            label="Signal phone number"
                            description="Enter your Signal phone number to receive notifications"
                          >
                            <Input
                              value={signalNumber}
                              onChange={({ detail }) => setSignalNumber(detail.value)}
                              placeholder="+1234567890"
                            />
                          </FormField>
                        )}
                      </SpaceBetween>
                    </ColumnLayout>
                  </SpaceBetween>
                </Form>
              )
            }
          ]}
        />
      </SpaceBetween>
    </Container>
  );
};

export default Preferences;
