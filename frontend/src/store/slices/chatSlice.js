import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import apiService from '../../services/api';

// Async thunks
export const fetchChatSessions = createAsyncThunk(
    'chat/fetchChatSessions',
    async (_, { rejectWithValue }) => {
        try {
            const response = await apiService.getChatSessions();
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const fetchChatHistory = createAsyncThunk(
    'chat/fetchChatHistory',
    async (sessionId, { rejectWithValue }) => {
        try {
            const response = await apiService.getChatHistory(sessionId);
            return { sessionId, messages: response.data };
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const createChatSession = createAsyncThunk(
    'chat/createChatSession',
    async (_, { rejectWithValue }) => {
        try {
            const response = await apiService.createChatSession();
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const sendChatMessage = createAsyncThunk(
    'chat/sendChatMessage',
    async ({ sessionId, message }, { rejectWithValue }) => {
        try {
            const response = await apiService.sendChatMessage(sessionId, message);
            return {
                sessionId,
                message: {
                    role: 'user',
                    content: message,
                    timestamp: new Date().toISOString()
                },
                response: {
                    role: 'bot',
                    content: response.data.response,
                    timestamp: new Date().toISOString(),
                    actions: response.data.actions || []
                }
            };
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

const initialState = {
    sessions: [],
    currentSession: null,
    messages: {},
    loading: false,
    error: null,
    isTyping: false,
    isChatOpen: false
};

const chatSlice = createSlice({
    name: 'chat',
    initialState,
    reducers: {
        clearChatError: (state) => {
            state.error = null;
        },
        setCurrentSession: (state, action) => {
            state.currentSession = action.payload;
        },
        toggleChat: (state) => {
            state.isChatOpen = !state.isChatOpen;
        },
        setTypingStatus: (state, action) => {
            state.isTyping = action.payload;
        },
        messageReceived: (state, action) => {
            const { sessionId, message } = action.payload;
            if (!state.messages[sessionId]) {
                state.messages[sessionId] = [];
            }
            state.messages[sessionId].push(message);
        },
        messageRead: (state, action) => {
            const { sessionId, messageId } = action.payload;
            if (state.messages[sessionId]) {
                const message = state.messages[sessionId].find(m => m.id === messageId);
                if (message) {
                    message.read = true;
                }
            }
        }
    },
    extraReducers: (builder) => {
        builder
            // Fetch Chat Sessions
            .addCase(fetchChatSessions.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchChatSessions.fulfilled, (state, action) => {
                state.loading = false;
                state.sessions = action.payload;
                // If there are sessions but no current session, set the first one as current
                if (action.payload.length > 0 && !state.currentSession) {
                    state.currentSession = action.payload[0].id;
                }
            })
            .addCase(fetchChatSessions.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Fetch Chat History
            .addCase(fetchChatHistory.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchChatHistory.fulfilled, (state, action) => {
                state.loading = false;
                const { sessionId, messages } = action.payload;
                state.messages[sessionId] = messages;
            })
            .addCase(fetchChatHistory.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Create Chat Session
            .addCase(createChatSession.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(createChatSession.fulfilled, (state, action) => {
                state.loading = false;
                state.sessions.push(action.payload);
                state.currentSession = action.payload.id;
                state.messages[action.payload.id] = [];
            })
            .addCase(createChatSession.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Send Chat Message
            .addCase(sendChatMessage.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(sendChatMessage.fulfilled, (state, action) => {
                state.loading = false;
                const { sessionId, message, response } = action.payload;
                if (!state.messages[sessionId]) {
                    state.messages[sessionId] = [];
                }
                state.messages[sessionId].push(message);
                state.messages[sessionId].push(response);
            })
            .addCase(sendChatMessage.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            });
    },
});

export const {
    clearChatError,
    setCurrentSession,
    toggleChat,
    setTypingStatus,
    messageReceived,
    messageRead
} = chatSlice.actions;

export default chatSlice.reducer;
