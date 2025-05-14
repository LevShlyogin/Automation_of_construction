import React from 'react';
import { Link } from '@tanstack/react-router';
import { Button, Container, Heading, Text } from '@chakra-ui/react';

const AboutPage: React.FC = () => {
  return (
    <Container centerContent py={10} textAlign="center">
      <Heading as="h1" size="lg" mb={4}>О программе</Heading>
      <Text mb={6}>Эта программа предназначена для расчета параметров турбин и их штоков.</Text>
      <Button as={Link} to="/" variant="primary">
        На главную
      </Button>
    </Container>
  );
};

export default AboutPage;
