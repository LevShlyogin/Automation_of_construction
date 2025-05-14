import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {
    Box,
    Heading,
    Input,
    List,
    ListItem,
    Spinner,
    Text,
    VStack,
    InputGroup,
} from '@chakra-ui/react';

import {TurbinesService, type TurbineInfo as ClientTurbineInfo} from '../../client';

type Turbine = ClientTurbineInfo;

type Props = {
    onSelectTurbine: (turbine: Turbine) => void;
};

const fetchTurbinesAPI = async () => {
    const turbinesResponse = await TurbinesService.turbinesGetAllTurbines();
    return turbinesResponse;
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
        <VStack spacing={6} p={5} align="stretch" w="100%" maxW="container.md" mx="auto">
            <Heading as="h2" size="lg" textAlign="center">
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
                            p={4}
                            borderWidth="1px"
                            borderRadius="md"
                            _hover={{bg: 'gray.100', cursor: 'pointer', shadow: 'md'}}
                            transition="background-color 0.2s, box-shadow 0.2s"
                        >
                            <Text fontSize="md" fontWeight="medium">{turbine.name}</Text>
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