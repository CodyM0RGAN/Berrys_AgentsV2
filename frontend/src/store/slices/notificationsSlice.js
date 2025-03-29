import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import apiService from '../../services/api';

// Async thunks
export const fetchNotifications = createAsyncThunk(
    'notifications/fetchNotifications',
    async (_, { rejectWithValue }) => {
        try {
            const response = await apiService.getNotifications();
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const markNotificationRead = createAsyncThunk(
    'notifications/markNotificationRead',
    async (id, { rejectWithValue }) => {
        try {
            await apiService.markNotificationRead(id);
            return id;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const markAllNotificationsRead = createAsyncThunk(
    'notifications/markAllNotificationsRead',
    async (_, { rejectWithValue }) => {
        try {
            await apiService.markAllNotificationsRead();
            return true;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const deleteNotification = createAsyncThunk(
    'notifications/deleteNotification',
    async (id, { rejectWithValue }) => {
        try {
            await apiService.deleteNotification(id);
            return id;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const fetchApprovals = createAsyncThunk(
    'notifications/fetchApprovals',
    async (_, { rejectWithValue }) => {
        try {
            const response = await apiService.getApprovals();
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const approveRequest = createAsyncThunk(
    'notifications/approveRequest',
    async (id, { rejectWithValue }) => {
        try {
            const response = await apiService.approveRequest(id);
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const rejectRequest = createAsyncThunk(
    'notifications/rejectRequest',
    async (id, { rejectWithValue }) => {
        try {
            const response = await apiService.rejectRequest(id);
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

const initialState = {
    notifications: [],
    unreadCount: 0,
    approvals: [],
    isDropdownOpen: false,
    loading: false,
    error: null,
};

const notificationsSlice = createSlice({
    name: 'notifications',
    initialState,
    reducers: {
        clearNotificationError: (state) => {
            state.error = null;
        },
        toggleNotificationsDropdown: (state) => {
            state.isDropdownOpen = !state.isDropdownOpen;
        },
        closeNotificationsDropdown: (state) => {
            state.isDropdownOpen = false;
        },
        notificationReceived: (state, action) => {
            state.notifications.unshift(action.payload);
            state.unreadCount += 1;
        },
        notificationUpdated: (state, action) => {
            const index = state.notifications.findIndex(n => n.id === action.payload.id);
            if (index !== -1) {
                // If the notification was unread and is now read, decrement the unread count
                if (!state.notifications[index].read && action.payload.read) {
                    state.unreadCount = Math.max(0, state.unreadCount - 1);
                }
                state.notifications[index] = action.payload;
            }
        },
        approvalCreated: (state, action) => {
            state.approvals.unshift(action.payload);
        },
        approvalUpdated: (state, action) => {
            const index = state.approvals.findIndex(a => a.id === action.payload.id);
            if (index !== -1) {
                state.approvals[index] = action.payload;
            }
        },
        approvalCompleted: (state, action) => {
            const index = state.approvals.findIndex(a => a.id === action.payload.id);
            if (index !== -1) {
                state.approvals[index] = action.payload;
            }
        },
    },
    extraReducers: (builder) => {
        builder
            // Fetch Notifications
            .addCase(fetchNotifications.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchNotifications.fulfilled, (state, action) => {
                state.loading = false;
                state.notifications = action.payload;
                state.unreadCount = action.payload.filter(n => !n.read).length;
            })
            .addCase(fetchNotifications.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Mark Notification Read
            .addCase(markNotificationRead.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(markNotificationRead.fulfilled, (state, action) => {
                state.loading = false;
                const notification = state.notifications.find(n => n.id === action.payload);
                if (notification && !notification.read) {
                    notification.read = true;
                    state.unreadCount = Math.max(0, state.unreadCount - 1);
                }
            })
            .addCase(markNotificationRead.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Mark All Notifications Read
            .addCase(markAllNotificationsRead.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(markAllNotificationsRead.fulfilled, (state) => {
                state.loading = false;
                state.notifications.forEach(notification => {
                    notification.read = true;
                });
                state.unreadCount = 0;
            })
            .addCase(markAllNotificationsRead.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Delete Notification
            .addCase(deleteNotification.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(deleteNotification.fulfilled, (state, action) => {
                state.loading = false;
                const notification = state.notifications.find(n => n.id === action.payload);
                if (notification && !notification.read) {
                    state.unreadCount = Math.max(0, state.unreadCount - 1);
                }
                state.notifications = state.notifications.filter(n => n.id !== action.payload);
            })
            .addCase(deleteNotification.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Fetch Approvals
            .addCase(fetchApprovals.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchApprovals.fulfilled, (state, action) => {
                state.loading = false;
                state.approvals = action.payload;
            })
            .addCase(fetchApprovals.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Approve Request
            .addCase(approveRequest.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(approveRequest.fulfilled, (state, action) => {
                state.loading = false;
                const index = state.approvals.findIndex(a => a.id === action.payload.id);
                if (index !== -1) {
                    state.approvals[index] = action.payload;
                }
            })
            .addCase(approveRequest.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Reject Request
            .addCase(rejectRequest.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(rejectRequest.fulfilled, (state, action) => {
                state.loading = false;
                const index = state.approvals.findIndex(a => a.id === action.payload.id);
                if (index !== -1) {
                    state.approvals[index] = action.payload;
                }
            })
            .addCase(rejectRequest.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            });
    },
});

export const {
    clearNotificationError,
    toggleNotificationsDropdown,
    closeNotificationsDropdown,
    notificationReceived,
    notificationUpdated,
    approvalCreated,
    approvalUpdated,
    approvalCompleted,
} = notificationsSlice.actions;

export default notificationsSlice.reducer;
