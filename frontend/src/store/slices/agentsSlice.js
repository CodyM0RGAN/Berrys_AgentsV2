import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import apiService from '../../services/api';

// Async thunks
export const fetchAgents = createAsyncThunk(
    'agents/fetchAgents',
    async (_, { rejectWithValue }) => {
        try {
            const response = await apiService.getAgents();
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const fetchAgent = createAsyncThunk(
    'agents/fetchAgent',
    async (id, { rejectWithValue }) => {
        try {
            const response = await apiService.getAgent(id);
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const createAgent = createAsyncThunk(
    'agents/createAgent',
    async (agentData, { rejectWithValue }) => {
        try {
            const response = await apiService.createAgent(agentData);
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const updateAgent = createAsyncThunk(
    'agents/updateAgent',
    async ({ id, data }, { rejectWithValue }) => {
        try {
            const response = await apiService.updateAgent(id, data);
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

export const deleteAgent = createAsyncThunk(
    'agents/deleteAgent',
    async (id, { rejectWithValue }) => {
        try {
            await apiService.deleteAgent(id);
            return id;
        } catch (error) {
            return rejectWithValue(error.response?.data?.message || error.message);
        }
    }
);

const initialState = {
    agents: [],
    currentAgent: null,
    loading: false,
    error: null,
};

const agentsSlice = createSlice({
    name: 'agents',
    initialState,
    reducers: {
        clearAgentError: (state) => {
            state.error = null;
        },
        clearCurrentAgent: (state) => {
            state.currentAgent = null;
        },
    },
    extraReducers: (builder) => {
        builder
            // Fetch Agents
            .addCase(fetchAgents.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchAgents.fulfilled, (state, action) => {
                state.loading = false;
                state.agents = action.payload;
            })
            .addCase(fetchAgents.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Fetch Agent
            .addCase(fetchAgent.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchAgent.fulfilled, (state, action) => {
                state.loading = false;
                state.currentAgent = action.payload;
            })
            .addCase(fetchAgent.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Create Agent
            .addCase(createAgent.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(createAgent.fulfilled, (state, action) => {
                state.loading = false;
                state.agents.push(action.payload);
            })
            .addCase(createAgent.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Update Agent
            .addCase(updateAgent.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(updateAgent.fulfilled, (state, action) => {
                state.loading = false;
                const index = state.agents.findIndex(agent => agent.id === action.payload.id);
                if (index !== -1) {
                    state.agents[index] = action.payload;
                }
                if (state.currentAgent?.id === action.payload.id) {
                    state.currentAgent = action.payload;
                }
            })
            .addCase(updateAgent.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Delete Agent
            .addCase(deleteAgent.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(deleteAgent.fulfilled, (state, action) => {
                state.loading = false;
                state.agents = state.agents.filter(agent => agent.id !== action.payload);
                if (state.currentAgent?.id === action.payload) {
                    state.currentAgent = null;
                }
            })
            .addCase(deleteAgent.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            });
    },
});

export const { clearAgentError, clearCurrentAgent } = agentsSlice.actions;

export default agentsSlice.reducer;
