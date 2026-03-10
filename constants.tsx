
import { ChatSession } from './types';

export const COLORS = {
  primary: '#3b82f6',
  secondary: '#10b981',
  accent: '#f59e0b',
  bg: '#f9fafb',
};

export const AD_SOURCES = [
  'Facebook Ads - Summer Campaign',
  'Instagram Influencer Link',
  'Google Search - Productivity Tool',
  'Direct Link'
];

export const INITIAL_SESSIONS: ChatSession[] = [
  {
    id: 'session-1',
    userId: 'user-1',
    userName: 'Sarah Jenkins',
    userAvatar: 'https://picsum.photos/seed/sarah/200',
    lastMessage: 'Hi, I saw your ad about the summer sale. Is it still active?',
    updatedAt: Date.now() - 3600000,
    status: 'OPEN',
    messages: [
      {
        id: 'msg-1',
        senderId: 'user-1',
        senderRole: 'USER',
        text: 'Hi, I saw your ad about the summer sale. Is it still active?',
        timestamp: Date.now() - 3600000,
        status: 'read',
      }
    ],
    adSource: 'Facebook Ads - Summer Campaign',
    unreadCount: 1,
    metadata: {
      browser: 'Chrome / MacOS',
      location: 'San Francisco, US',
      ip: '192.168.1.45',
      adId: 'FB_SUMMER_2024_01'
    }
  },
  {
    id: 'session-2',
    userId: 'user-2',
    userName: 'Marcus Rivera',
    userAvatar: 'https://picsum.photos/seed/marcus/200',
    lastMessage: 'Do you offer international shipping?',
    updatedAt: Date.now() - 7200000,
    status: 'RESOLVED',
    messages: [
      {
        id: 'msg-2',
        senderId: 'user-2',
        senderRole: 'USER',
        text: 'Do you offer international shipping?',
        timestamp: Date.now() - 7200000,
        status: 'read',
      }
    ],
    adSource: 'Instagram Influencer Link',
    unreadCount: 0,
    metadata: {
      browser: 'Safari / iPhone',
      location: 'Madrid, ES',
      ip: '82.14.99.12',
      adId: 'INSTA_INFLUENCE_JUNE'
    }
  }
];
