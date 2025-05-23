import {Box, Container, Text, Heading} from "@chakra-ui/react";
import {createFileRoute} from "@tanstack/react-router";

function DashboardPage() {
    return (
        <Container maxW="full">
            <Box pt={12} m={4}>
                <Heading size="xl" mb={4}>Добро пожаловать!</Heading>
                <Text fontSize="lg">
                    Это главная страница WSAPropertiesCalculator.
                </Text>
                <Text mt={2}>
                    Используйте навигацию для перехода к калькулятору или другим разделам.
                </Text>
            </Box>
        </Container>
    );
}

export const Route = createFileRoute('/')({
    component: DashboardPage,
});