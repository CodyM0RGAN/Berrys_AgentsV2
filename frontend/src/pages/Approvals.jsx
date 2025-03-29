import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import ApprovalCard from '../components/Approvals/ApprovalCard';
import { fetchApprovals } from '../store/slices/notificationsSlice';

const Approvals = () => {
    const dispatch = useDispatch();
    const { approvals, loading, error } = useSelector(state => state.notifications);

    useEffect(() => {
        dispatch(fetchApprovals());
    }, [dispatch]);

    // Filter approvals by status
    const pendingApprovals = approvals.filter(approval => approval.status === 'pending');
    const completedApprovals = approvals.filter(approval => approval.status !== 'pending');

    return (
        <div className="container mx-auto px-4 py-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Approval Requests</h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Review and manage approval requests from across the system.
                </p>
            </div>

            {/* Error message */}
            {error && (
                <div className="mb-6 p-4 bg-red-100 border-l-4 border-red-500 text-red-700 dark:bg-red-900/30 dark:text-red-400 dark:border-red-500">
                    <p className="font-medium">Error loading approvals</p>
                    <p>{error}</p>
                </div>
            )}

            {/* Loading state */}
            {loading ? (
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-white"></div>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-6">
                    {/* Pending Approvals Section */}
                    <section>
                        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
                            Pending Approvals {pendingApprovals.length > 0 && `(${pendingApprovals.length})`}
                        </h2>

                        {pendingApprovals.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {pendingApprovals.map(approval => (
                                    <ApprovalCard key={approval.id} approval={approval} />
                                ))}
                            </div>
                        ) : (
                            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 text-center">
                                <p className="text-gray-600 dark:text-gray-400">No pending approvals</p>
                            </div>
                        )}
                    </section>

                    {/* Completed Approvals Section */}
                    {completedApprovals.length > 0 && (
                        <section className="mt-8">
                            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
                                Completed Approvals
                            </h2>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {completedApprovals.map(approval => (
                                    <ApprovalCard key={approval.id} approval={approval} />
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            )}
        </div>
    );
};

export default Approvals;
