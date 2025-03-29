import { useParams } from 'react-router-dom';
import PlaceholderPage from '../components/PlaceholderPage';

/**
 * TaskDetail page component
 * 
 * @returns {JSX.Element} - TaskDetail page
 */
const TaskDetail = () => {
    const { id } = useParams();
    return <PlaceholderPage title={`Task Details: ${id}`} />;
};

export default TaskDetail;
