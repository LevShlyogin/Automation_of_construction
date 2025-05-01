import { createFileRoute } from '@tanstack/react-router';
import AboutPage from '../components/OtherPages/AboutPage';

export const Route = createFileRoute('/about')({
  component: AboutPage,
});
