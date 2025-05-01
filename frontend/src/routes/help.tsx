import { createFileRoute } from '@tanstack/react-router';
import HelpPage from '../components/OtherPages/HelpPage';

export const Route = createFileRoute('/help')({
  component: HelpPage,
});
