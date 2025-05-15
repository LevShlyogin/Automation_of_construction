import React, {useState} from 'react';
import * as XLSX from 'xlsx';
import {
    Box,
    Button,
    Heading,
    Text,
    VStack,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    TableContainer,
    SimpleGrid,
    Divider,
    HStack,
    useToast,
} from '@chakra-ui/react';

import {
    type CalculationParams,
} from '../../client';

interface ExpectedOutputData {
    Gi?: number[];
    Pi_in?: number[];
    Ti?: number[];
    Hi?: number[];
    deaerator_props?: any[];
    ejector_props?: Array<Record<string, number>>;
}

type Props = {
    stockId: string;
    inputData?: Partial<CalculationParams>;
    outputData?: Partial<ExpectedOutputData>;
    onGoBack?: () => void;
};

const roundNumber = (num: any, decimals: number = 4): string | number => {
    const parsedNum = parseFloat(num);
    if (isNaN(parsedNum)) {
        return 'N/A';
    }
    return Number(parsedNum.toFixed(decimals));
};

const ResultsPage: React.FC<Props> = ({stockId, inputData = {}, outputData = {}, onGoBack}) => {
    const [isSavedMessageVisible, setIsSavedMessageVisible] = useState(false);
    const toast = useToast();

    const currentInputData: Partial<CalculationParams> = inputData || {};
    const currentOutputData: Partial<ExpectedOutputData> = outputData || {};

    const inputDataEntries = [
        {label: 'Название турбины', value: currentInputData.turbine_name},
        {label: 'Чертёж клапана', value: currentInputData.valve_drawing},
        {label: 'ID клапана', value: currentInputData.valve_id},
        {label: 'Начальная температура (°C)', value: currentInputData.temperature_start},
        {label: 'Температура воздуха (°C)', value: currentInputData.t_air},
        {label: 'Количество клапанов', value: currentInputData.count_valves},
        {
            label: 'Входные давления (P1-P5, МПа)',
            value: Array.isArray(currentInputData.p_values) ? currentInputData.p_values.join(', ') : 'N/A'
        },
        {
            label: 'Давления потребителей (МПа)',
            value: Array.isArray(currentInputData.p_ejector) ? currentInputData.p_ejector.join(', ') : 'N/A'
        },
    ];

    const gi = Array.isArray(currentOutputData.Gi) ? currentOutputData.Gi : [];
    const pi_in = Array.isArray(currentOutputData.Pi_in) ? currentOutputData.Pi_in : [];
    const ti = Array.isArray(currentOutputData.Ti) ? currentOutputData.Ti : [];
    const hi = Array.isArray(currentOutputData.Hi) ? currentOutputData.Hi : [];
    const deaeratorProps = Array.isArray(currentOutputData.deaerator_props) ? currentOutputData.deaerator_props : [];
    const ejectorProps = Array.isArray(currentOutputData.ejector_props) ? currentOutputData.ejector_props : [];

    const handleDownloadExcel = () => {
        try {
            const wb = XLSX.utils.book_new();

            if (Object.keys(currentInputData).length > 0) {
                const inputSheetData = [{
                    'Название турбины': currentInputData.turbine_name,
                    'Чертёж клапана': currentInputData.valve_drawing,
                    'ID клапана': currentInputData.valve_id,
                    'Начальная температура': currentInputData.temperature_start,
                    'Температура воздуха': currentInputData.t_air,
                    'Количество клапанов': currentInputData.count_valves,
                    'Выходные давления (P_ejector)': Array.isArray(currentInputData.p_ejector) ? currentInputData.p_ejector.join(', ') : '',
                    'Входные давления (P_values)': Array.isArray(currentInputData.p_values) ? currentInputData.p_values.join(', ') : '',
                }];
                const inputWs = XLSX.utils.json_to_sheet(inputSheetData);
                XLSX.utils.book_append_sheet(wb, inputWs, 'Входные данные');
            }

            if (gi.length > 0) {
                const mainOutputData = gi.map((_g: number, index: number) => ({
                    'Расход, т/ч': roundNumber(gi[index]),
                    'Давление, МПа': roundNumber(pi_in[index]),
                    'Температура, °C': roundNumber(ti[index]),
                    'Энтальпия, кДж/кг': roundNumber(hi[index]),
                }));
                const mainOutputWs = XLSX.utils.json_to_sheet(mainOutputData);
                XLSX.utils.book_append_sheet(wb, mainOutputWs, 'Основные выходные');
            }

            if (ejectorProps.length > 0) {
                const ejectorSheetData = ejectorProps.map(prop => {
                    const row: { [key: string]: string | number } = {};
                    if (prop && typeof prop === 'object') {
                        for (const key in prop) {
                            row[key] = roundNumber(prop[key]);
                        }
                    }
                    return row;
                });
                const ejectorWs = XLSX.utils.json_to_sheet(ejectorSheetData);
                XLSX.utils.book_append_sheet(wb, ejectorWs, 'Параметры эжекторов');
            }

            if (deaeratorProps.length > 0) {
                const deaeratorSheetData = [{
                    'Параметр 1': roundNumber(deaeratorProps[0]),
                    'Параметр 2': roundNumber(deaeratorProps[1]),
                    'Параметр 3': roundNumber(deaeratorProps[2]),
                    'Параметр 4': roundNumber(deaeratorProps[3]),
                }];
                const deaeratorWs = XLSX.utils.json_to_sheet(deaeratorSheetData);
                XLSX.utils.book_append_sheet(wb, deaeratorWs, 'Параметры деаэратора');
            }

            XLSX.writeFile(wb, `Расчет_${stockId || 'клапана'}.xlsx`);
            toast({title: "Excel файл успешно создан!", status: "success", duration: 3000, isClosable: true});
        } catch (e: any) {
            console.error("Ошибка при создании Excel:", e);
            toast({
                title: "Ошибка при создании Excel",
                description: e?.message || String(e),
                status: "error",
                duration: 5000,
                isClosable: true
            });
        }
    };

    const handleShowSavedMessage = () => {
        setIsSavedMessageVisible(true);
        setTimeout(() => setIsSavedMessageVisible(false), 4000);
    };

    return (
        <VStack spacing={6} p={5} align="stretch" w="100%" maxW="container.xl" mx="auto">
            <Heading as="h2" size="xl" textAlign="center">
                Результаты расчётов для клапана: <Text as="span" color="teal.500">{stockId}</Text>
            </Heading>

            {onGoBack && (
                <Box textAlign="left" width="100%">
                    <Button onClick={onGoBack} variant="link" colorScheme="teal" size="sm" mb={2}>
                        ← Вернуться к вводу данных
                    </Button>
                </Box>
            )}

            <Box borderWidth="1px" borderRadius="md" p={4}>
                <Heading as="h3" size="lg" mb={4}>Входные данные:</Heading>
                {Object.keys(currentInputData).length > 0 ? (
                    <SimpleGrid columns={{base: 1, md: 2}} spacing={3}>
                        {inputDataEntries.map(entry => (
                            (entry.value !== undefined && entry.value !== null && entry.value !== '') &&
                            <HStack key={entry.label} justify="space-between">
                                <Text fontWeight="medium">{entry.label}:</Text>
                                <Text>{String(entry.value)}</Text>
                            </HStack>
                        ))}
                    </SimpleGrid>
                ) : (
                    <Text color="gray.500">Нет доступных входных данных.</Text>
                )}
            </Box>

            <Divider my={6}/>

            <Heading as="h3" size="lg" mb={4} textAlign="center">Выходные данные:</Heading>

            {gi.length > 0 ? (
                <TableContainer borderWidth="1px" borderRadius="md" mb={6}>
                    <Table variant="striped" colorScheme="gray" size="md">
                        <Thead>
                            <Tr>
                                <Th>Расход, т/ч (G<sub>i</sub>)</Th>
                                <Th>Давление, МПа (P<sub>вхi</sub>)</Th>
                                <Th>Температура, °C (T<sub>i</sub>)</Th>
                                <Th>Энтальпия, кДж/кг (H<sub>i</sub>)</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {gi.map((_value: number, index: number) => (
                                <Tr key={`gi-res-${index}`}>
                                    <Td>{roundNumber(gi[index])}</Td>
                                    <Td>{roundNumber(pi_in[index])}</Td>
                                    <Td>{roundNumber(ti[index])}</Td>
                                    <Td>{roundNumber(hi[index])}</Td>
                                </Tr>
                            ))}
                        </Tbody>
                    </Table>
                </TableContainer>
            ) : (
                <Text color="gray.500" textAlign="center" mb={6}>Нет основных выходных данных.</Text>
            )}

            {ejectorProps.length > 0 && (
                <Box mb={6}>
                    <Heading as="h4" size="md" mb={2}>Параметры потребителей (эжекторы):</Heading>
                    <TableContainer borderWidth="1px" borderRadius="md">
                        <Table variant="simple" size="sm">
                            <Thead>
                                <Tr>
                                    {ejectorProps[0] && typeof ejectorProps[0] === 'object' && Object.keys(ejectorProps[0]).map(key =>
                                        <Th key={`th-ejector-${key}`}>{key.toUpperCase()}</Th>)}
                                </Tr>
                            </Thead>
                            <Tbody>
                                {ejectorProps.map((prop, index: number) => (
                                    <Tr key={`ejector-res-${index}`}>
                                        {typeof prop === 'object' && prop !== null && Object.values(prop).map((val, idx: number) => (
                                            <Td key={`td-ejector-${index}-${idx}`}>{roundNumber(val)}</Td>
                                        ))}
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </TableContainer>
                </Box>
            )}

            {deaeratorProps.length > 0 && (
                <Box mb={6}>
                    <Heading as="h4" size="md" mb={2}>Потребитель 1 (деаэратор):</Heading>
                    <Text borderWidth="1px" borderRadius="md" p={3}>
                        {deaeratorProps.map((val: any, idx: number) => `Парам. ${idx + 1}: ${roundNumber(val)}`).join('; ')}
                    </Text>
                </Box>
            )}

            <HStack spacing={4} justifyContent="center" mt={8}>
                <Button onClick={handleDownloadExcel} colorScheme="green" variant="solid" size="lg" minW="220px">
                    Сохранить в виде Excel
                </Button>
                <Button
                    onClick={handleShowSavedMessage}
                    colorScheme="blue"
                    variant="outline"
                    size="lg"
                    minW="220px"
                >
                    Сохранено в базе данных
                </Button>
            </HStack>
            {isSavedMessageVisible && (
                <Text textAlign="center" color="green.500" mt={3} fontWeight="bold">
                    Данные этого расчета уже сохранены в базе данных при его выполнении.
                </Text>
            )}
        </VStack>
    );
};

export default ResultsPage;