import {Box, Flex, Image, Text, Link as ChakraLink, Icon, HStack} from "@chakra-ui/react";
import {Outlet, createFileRoute, Link as RouterLink} from "@tanstack/react-router";
import {FiHome, FiHelpCircle, FiInfo} from "react-icons/fi";

import Sidebar from "../components/Common/Sidebar";

export const Route = createFileRoute("/_layout")({
    component: Layout,
});

function Layout() {
    return (
        <Flex direction="column" minH="100vh">
            <Flex
                as="header"
                align="center"
                justify="space-between"
                p={4}
                bg="gray.100"
                boxShadow="sm"
                wrap="wrap"
            >
                <Flex align="center">
                    <Image src="/logo.png" alt="Logo" boxSize="40px" mr={3}/>
                    <Text fontSize="xl" fontWeight="bold">
                        WSAPropertiesCalculator
                    </Text>
                </Flex>
                <HStack as="nav" spacing={4}>
                    <ChakraLink as={RouterLink} to="/calculator" display="flex" alignItems="center"
                                _activeLink={{fontWeight: "bold", color: "teal.500"}}>
                        <Icon as={FiHome} mr={1}/> Калькулятор
                    </ChakraLink>
                    <ChakraLink as={RouterLink} to="/about" display="flex" alignItems="center"
                                _activeLink={{fontWeight: "bold", color: "teal.500"}}>
                        <Icon as={FiInfo} mr={1}/> О программе
                    </ChakraLink>
                    <ChakraLink as={RouterLink} to="/help" display="flex" alignItems="center"
                                _activeLink={{fontWeight: "bold", color: "teal.500"}}>
                        <Icon as={FiHelpCircle} mr={1}/> Помощь
                    </ChakraLink>
                </HStack>
            </Flex>

            <Flex flex="1" h="auto" position="relative">
                <Sidebar/>
                <Box flex="1" p={4} as="main">
                    <Outlet/>
                </Box>
            </Flex>

            <Box as="footer" bg="gray.100" p={4} textAlign="center" boxShadow="inner">
                <Text fontSize="sm">
                    © WSAPropsCalculator. АО "Уральский турбинный завод", 2024-2025.
                </Text>
            </Box>
        </Flex>
    );
}