import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {
    Box,
    Heading,
    Input,
    InputGroup,
    List,
    ListItem,
    Spinner,
    Text,
    useColorModeValue,
    VStack,
} from '@chakra-ui/react';

import {type TurbineInfo as ClientTurbineInfo, TurbinesService} from '../../client';

type Turbine = ClientTurbineInfo;

type Props = {
    onSelectTurbine: (turbine: Turbine) => void;
};

const fetchTurbinesAPI = async () => {
    return TurbinesService.turbinesGetAllTurbines();
};

const TurbineSearch: React.FC<Props> = ({onSelectTurbine}) => {
    const [searchTerm, setSearchTerm] = useState('');

    const {
        data: turbines,
        isLoading,
        isError,
        error,
    } = useQuery<Turbine[], Error>({
        queryKey: ['turbines'],
        queryFn: fetchTurbinesAPI,
    });

    const listItemHoverBg = useColorModeValue('gray.100', 'gray.700');
    const listItemHoverColor = useColorModeValue('gray.800', 'white');

    const filteredTurbines = turbines?.filter(turbine =>
        turbine.name.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    if (isLoading) {
        return (
            <VStack spacing={4} align="center" justify="center" minH="200px">
                <Spinner size="xl" color="teal.500"/>
                <Text>Загрузка турбин...</Text>
            </VStack>
        );
    }

    if (isError) {
        return (
            <VStack spacing={4} align="center" justify="center" minH="200px" color="red.500">
                <Text fontSize="lg" fontWeight="bold">Ошибка при загрузке данных:</Text>
                <Text>{error?.message || 'Произошла неизвестная ошибка'}</Text>
            </VStack>
        );
    }

    return (
        <VStack spacing={6} p={5} align="stretch" w="100%" maxW="container.lg" mx="auto">
            <Heading as="h2" size="xl" textAlign="center" mb={2}>
                Введите название турбины
            </Heading>

            <Box>
                <InputGroup size="lg">
                    <Input
                        type="text"
                        placeholder="Например, A-100"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        focusBorderColor="teal.500"
                        variant="filled"
                    />
                </InputGroup>
            </Box>

            {turbines && turbines.length > 0 ? (
                <List spacing={3} w="100%">
                    {filteredTurbines.map((turbine) => (
                        <ListItem
                            key={turbine.id}
                            onClick={() => onSelectTurbine(turbine)}
                            p={5}
                            borderWidth="1px"
                            borderRadius="lg"
                            borderColor={useColorModeValue("gray.200", "gray.600")}
                            bg={useColorModeValue("white", "gray.750")}
                            boxShadow="base"
                            _hover={{
                                bg: listItemHoverBg,
                                color: listItemHoverColor,
                                cursor: 'pointer',
                                shadow: 'md',
                                borderColor: useColorModeValue("teal.300", "teal.500"),
                            }}
                            transition="all 0.2s ease-in-out"
                        >
                            <Text fontSize="lg" fontWeight="medium">{turbine.name}</Text>
                        </ListItem>
                    ))}
                    {filteredTurbines.length === 0 && searchTerm && (
                        <ListItem textAlign="center" color="gray.500" p={4}>
                            Турбины не найдены по вашему запросу.
                        </ListItem>
                    )}
                </List>
            ) : (
                <Text textAlign="center" color="gray.500" p={4}>
                    Нет доступных турбин.
                </Text>
            )}
        </VStack>
    );
};

export default TurbineSearch;