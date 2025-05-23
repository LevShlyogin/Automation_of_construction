import {
    Box,
    Flex,
    Image,
    Text,
    Link as ChakraLink,
    Icon,
    HStack,
    useColorModeValue,
    Stack,
} from '@chakra-ui/react';
import {Outlet, Link as RouterLink} from '@tanstack/react-router';
import {FiGrid, FiCode, FiHelpCircle, FiInfo} from 'react-icons/fi';

import Sidebar from './Sidebar';
import {ThemeToggleButton} from './ThemeToggleButton';

export default function MainLayout() {
    const headerBg = useColorModeValue('white', 'gray.800');
    const headerBorderColor = useColorModeValue('gray.200', 'gray.700');
    const footerBg = useColorModeValue('gray.50', 'gray.900');
    const linkColor = useColorModeValue('gray.600', 'gray.200');
    const activeLinkColor = useColorModeValue('teal.500', 'teal.300');
    const activeLinkBg = useColorModeValue('teal.50', 'gray.700');

    const navLinks = [
        {to: "/", label: "Главная", icon: FiGrid},
        {to: "/calculator", label: "Калькулятор", icon: FiCode},
        {to: "/about", label: "О программе", icon: FiInfo},
        {to: "/help", label: "Помощь", icon: FiHelpCircle},
    ];

    return (
        <Flex direction="column" minH="100vh">
            <Flex
                as="header"
                align="center"
                justify="space-between"
                py={3}
                px={6}
                bg={headerBg}
                borderBottomWidth="1px"
                borderColor={headerBorderColor}
                boxShadow="sm"
                wrap="wrap"
            >
                <Flex align="center" as={RouterLink} to="/" _hover={{textDecoration: 'none'}}>
                    <Image src="/logo.png" alt="WSA Logo" boxSize="36px" mr={3}/>
                    <Text fontSize="lg" fontWeight="bold" color={useColorModeValue('gray.700', 'white')}>
                        WSAPropertiesCalculator
                    </Text>
                </Flex>

                <Stack direction="row" spacing={{base: 2, md: 4}} align="center">
                    <HStack as="nav" spacing={{base: 2, md: 4}}>
                        {navLinks.map(link => (
                            <ChakraLink
                                key={link.to}
                                as={RouterLink}
                                to={link.to}
                                display="flex"
                                alignItems="center"
                                p={2}
                                borderRadius="md"
                                fontWeight="medium"
                                color={linkColor}
                                _hover={{
                                    textDecoration: 'none',
                                    bg: useColorModeValue('gray.100', 'gray.700'),
                                    color: activeLinkColor,
                                }}
                                activeProps={{
                                    style: {
                                        fontWeight: 'bold',
                                        color: activeLinkColor,
                                        backgroundColor: activeLinkBg,
                                    }
                                }}
                            >
                                <Icon as={link.icon} mr={{base: 0, md: 2}} boxSize={5}/>
                                <Text display={{base: 'none', md: 'inline'}}>{link.label}</Text>
                            </ChakraLink>
                        ))}
                    </HStack>

                    <ThemeToggleButton/>
                </Stack>
            </Flex>

            <Flex
                flex="1"
                h="auto"
            >
                <Sidebar/>
                <Box
                    flex="1"
                    p={{base: 4, md: 6}}
                    as="main"
                    overflowY="auto"
                >
                    <Outlet/>
                </Box>
            </Flex>

            <Box
                as="footer"
                bg={footerBg}
                py={4}
                px={6}
                textAlign="center"
                borderTopWidth="1px"
                borderColor={headerBorderColor}
            >
                <Text fontSize="sm" color={useColorModeValue('gray.600', 'gray.400')}>
                    © WSAPropsCalculator. АО «Уральский турбинный завод», 2024-2025.
                </Text>
            </Box>
        </Flex>
    );
}