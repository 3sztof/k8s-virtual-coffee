import React, { createContext, useState, useContext, ReactNode } from 'react';
import { Flashbar, FlashbarProps } from '@cloudscape-design/components';

// Define types
interface NotificationContextType {
  addNotification: (notification: FlashbarProps.MessageDefinition) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

// Create context
const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

// Provider component
export const NotificationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<FlashbarProps.MessageDefinition[]>([]);

  // Add notification
  const addNotification = (notification: FlashbarProps.MessageDefinition) => {
    // Ensure notification has an id
    const notificationWithId = {
      ...notification,
      id: notification.id || `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      dismissible: notification.dismissible !== false
    };
    
    setNotifications(prev => [...prev, notificationWithId]);
    
    // Auto-dismiss after timeout if specified
    if (notification.dismissible !== false && notification.autoDismiss) {
      setTimeout(() => {
        removeNotification(notificationWithId.id as string);
      }, notification.autoDismiss);
    }
  };

  // Remove notification
  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  // Clear all notifications
  const clearNotifications = () => {
    setNotifications([]);
  };

  return (
    <NotificationContext.Provider value={{ addNotification, removeNotification, clearNotifications }}>
      <div className="notification-container">
        {notifications.length > 0 && (
          <Flashbar items={notifications} />
        )}
      </div>
      {children}
    </NotificationContext.Provider>
  );
};

// Custom hook to use notification context
export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};