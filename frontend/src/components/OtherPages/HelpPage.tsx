import React from 'react';
import { Link } from '@tanstack/react-router';
import { Button, Container, Heading, Text } from '@chakra-ui/react';

const HelpPage: React.FC = () => {
  return (
    <Container centerContent py={10} textAlign="center">
        <Heading as="h1" size="lg" mb={4}>Помощь</Heading>
        <Text mb={6}>Здесь вы найдете ответы на часто задаваемые вопросы и инструкцию по использованию.</Text>
        <Button as={Link} to="/" variant="primary">
            На главную
        </Button>
    </Container>
  );
};

export default HelpPage;
