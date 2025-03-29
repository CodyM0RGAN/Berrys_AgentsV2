import { formatDistanceToNow } from 'date-fns';
import PropTypes from 'prop-types';
import { useDispatch } from 'react-redux';
import { approveRequest, rejectRequest } from '../../store/slices/notificationsSlice';

const ApprovalCard = ({ approval }) => {
    const dispatch = useDispatch();
    const { id, title, description, status, createdAt, metadata } = approval;

    // Format the time (e.g., "2 hours ago")
    const timeAgo = formatDistanceToNow(new Date(createdAt), { addSuffix: true });

    const handleApprove = () => {
        dispatch(approveRequest(id));
    };

    const handleReject = () => {
        dispatch(rejectRequest(id));
    };

    // Determine status badge color
    const getStatusBadge = () => {
        switch (status) {
            case 'pending':
                return (
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300">
                        Pending
                    </span>
                );
            case 'approved':
                return (
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                        Approved
                    </span>
                );
            case 'rejected':
                return (
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300">
                        Rejected
                    </span>
                );
            default:
                return null;
        }
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="p-4">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">{title}</h3>
                    {getStatusBadge()}
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">{description}</p>

                {/* Metadata display - can be customized based on approval type */}
                {metadata && Object.keys(metadata).length > 0 && (
                    <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Details</h4>
                        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                            {Object.entries(metadata).map(([key, value]) => (
                                <div key={key} className="col-span-2">
                                    <dt className="text-gray-500 dark:text-gray-400 inline">{key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}: </dt>
                                    <dd className="text-gray-900 dark:text-gray-100 inline">{typeof value === 'object' ? JSON.stringify(value) : value.toString()}</dd>
                                </div>
                            ))}
                        </dl>
                    </div>
                )}

                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>Requested {timeAgo}</span>
                    {approval.requestedBy && (
                        <span>by {approval.requestedBy}</span>
                    )}
                </div>
            </div>

            {status === 'pending' && (
                <div className="flex border-t border-gray-200 dark:border-gray-700 divide-x divide-gray-200 dark:divide-gray-700">
                    <button
                        className="flex-1 px-4 py-2 text-sm font-medium text-green-600 hover:text-green-800 hover:bg-green-50 dark:text-green-400 dark:hover:text-green-300 dark:hover:bg-green-900/30 transition-colors"
                        onClick={handleApprove}
                    >
                        Approve
                    </button>
                    <button
                        className="flex-1 px-4 py-2 text-sm font-medium text-red-600 hover:text-red-800 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-900/30 transition-colors"
                        onClick={handleReject}
                    >
                        Reject
                    </button>
                </div>
            )}
        </div>
    );
};

ApprovalCard.propTypes = {
    approval: PropTypes.shape({
        id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
        title: PropTypes.string.isRequired,
        description: PropTypes.string.isRequired,
        status: PropTypes.oneOf(['pending', 'approved', 'rejected']).isRequired,
        createdAt: PropTypes.string.isRequired,
        metadata: PropTypes.object,
        requestedBy: PropTypes.string
    }).isRequired
};

export default ApprovalCard;
