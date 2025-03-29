import { useParams } from 'react-router-dom';
import PlaceholderPage from '../components/PlaceholderPage';

/**
 * ResultDetail page component
 * 
 * @returns {JSX.Element} - ResultDetail page
 */
const ResultDetail = () => {
    const { id } = useParams();
    return <PlaceholderPage title={`Result Details: ${id}`} />;
};

export default ResultDetail;
