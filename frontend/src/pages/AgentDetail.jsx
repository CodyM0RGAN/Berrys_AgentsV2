import { useParams } from 'react-router-dom';
import PlaceholderPage from '../components/PlaceholderPage';

/**
 * AgentDetail page component
 * 
 * @returns {JSX.Element} - AgentDetail page
 */
const AgentDetail = () => {
    const { id } = useParams();
    return <PlaceholderPage title={`Agent Details: ${id}`} />;
};

export default AgentDetail;
