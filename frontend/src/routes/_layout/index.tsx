import {Box, Container, Text} from "@chakra-ui/react";
import {createFileRoute, redirect} from "@tanstack/react-router";

export const Route = createFileRoute("/_layout/")({
    component: Dashboard,
    loader: () => {
        throw redirect({to: '/calculator'});
    }
});

function Dashboard() {

    return (
        <>
            <Container maxW="full">
                <Box pt={12} m={4}>
                    <Text>WSAPropertiesCalculator</Text>
                </Box>
            </Container>
        </>
    );
}