// FRONTEND\SRC\components\Calculator\ResultsPage.tsx (новая версия)
import React, {useState} // Убрали useEffect, т.к. данные приходят как пропсы
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
    useToast, // Для уведомлений, если понадобятся
} from '@chakra-ui/react';

// Типы для inputData и outputData должны соответствовать тому, как они хранятся
// в CalculationDataType (т.е. как объекты, а не строки JSON)
// Предполагаем, что это CalculationParams и CalculationResult из schemas.py бэкенда
import {type CalculationParams, type CalculationResult} from '../../client';

// Убрали импорт './ResultsPage.css';

type Props = {
    stockId: string;
    inputData?: Partial<CalculationParams>; // Partial, так как могут быть не все поля или undefined
    outputData?: Partial<CalculationResult>;
    onGoBack?: () => void; // Для возврата к вводу данных или выбору штока
};

// Функция округления
const roundNumber = (num: number | undefined | null, decimals: number = 4): string | number => {
    if (num === undefined || num === null || isNaN(num)) {
        return 'N/A';
    }
    return Number(num.toFixed(decimals));
};

const ResultsPage: React.FC<Props> = ({stockId, inputData = {}, outputData = {}, onGoBack}) => {
    const [isSavedMessageVisible, setIsSavedMessageVisible] = useState(false); // Для сообщения о "сохранении"
    const toast = useToast();

    const inputDataEntries = [
        {label: 'Название турбины', value: inputData.turbine_name},
        {label: 'Чертёж клапана', value: inputData.valve_drawing},
        {label: 'ID клапана', value: inputData.valve_id},
        {label: 'Начальная температура (°C)', value: inputData.temperature_start},
        {label: 'Температура воздуха (°C)', value: inputData.t_air},
        {label: 'Количество клапанов', value: inputData.count_valves},
        {label: 'Входные давления (P1-P5, МПа)', value: (inputData.p_values || []).join(', ')},
        {label: 'Давления потребителей (МПа)', value: (inputData.p_ejector || []).join(', ')},
    ];

    // Основные выходные данные
    const gi = outputData.Gi || [];
    const pi_in = outputData.Pi_in || [];
    const ti = outputData.Ti || [];
    const hi = outputData.Hi || [];
    // Данные потребителей
    const deaeratorProps = outputData.deaerator_props || [];
    const ejectorProps = outputData.ejector_props || [];

    // Функция для преобразования данных в плоский формат для Excel
    // (оставляем без изменений, если она работала)
    const flattenDataForExcel = (data: Record<string, any>, headersOrder?: string[]): any[] => {
        const result: any[] = [];
        const keys = headersOrder || Object.keys(data); // Используем порядок заголовков, если предоставлен
        const maxLength = Math.max(1, ...keys.map(key => Array.isArray(data[key]) ? data[key].length : 1));

        for (let i = 0; i < maxLength; i++) {
            const row: any = {};
            keys.forEach(key => {
                const value = data[key];
                if (Array.isArray(value)) {
                    row[key] = value[i] !== undefined ? value[i] : '';
                } else if (i === 0) { // Для не-массивов значение только в первой строке
                    row[key] = value !== undefined ? value : '';
                } else {
                    row[key] = ''; // Пусто для остальных строк не-массивов
                }
            });
            result.push(row);
        }
        return result;
    };

    const handleDownloadExcel = () => {
        try {
            const wb = XLSX.utils.book_new();

            // Входные данные
            if (Object.keys(inputData).length > 0) {
                const inputSheetData = [{ // Создаем одну строку для входных данных
                    'Название турбины': inputData.turbine_name,
                    'Чертёж клапана': inputData.valve_drawing,
                    'ID клапана': inputData.valve_id,
                    'Начальная температура': inputData.temperature_start,
                    'Температура воздуха': inputData.t_air,
                    'Количество клапанов': inputData.count_valves,
                    'Выходные давления (P_ejector)': (inputData.p_ejector || []).join(', '),
                    'Входные давления (P_values)': (inputData.p_values || []).join(', '),
                }];
                const inputWs = XLSX.utils.json_to_sheet(inputSheetData);
                XLSX.utils.book_append_sheet(wb, inputWs, 'Входные данные');
            }

            // Основные выходные данные (Gi, Pi_in, Ti, Hi)
            if (gi.length > 0) {
                const mainOutputData = gi.map((_g, index) => ({
                    'Расход, т/ч': roundNumber(gi[index]),
                    'Давление, МПа': roundNumber(pi_in[index]),
                    'Температура, °C': roundNumber(ti[index]),
                    'Энтальпия, кДж/кг': roundNumber(hi[index]),
                }));
                const mainOutputWs = XLSX.utils.json_to_sheet(mainOutputData);
                XLSX.utils.book_append_sheet(wb, mainOutputWs, 'Основные выходные');
            }

            // Параметры эжекторов
            if (ejectorProps.length > 0) {
                const ejectorSheetData = ejectorProps.map(prop => {
                    const row: { [key: string]: string | number } = {};
                    for (const key in prop) {
                        row[key] = roundNumber(prop[key]);
                    }
                    return row;
                });
                const ejectorWs = XLSX.utils.json_to_sheet(ejectorSheetData);
                XLSX.utils.book_append_sheet(wb, ejectorWs, 'Параметры эжекторов');
            }

            // Параметры деаэратора
            if (deaeratorProps.length > 0) {
                const deaeratorSheetData = [{ // Обычно это набор скалярных значений
                    'Параметр 1': roundNumber(deaeratorProps[0]),
                    'Параметр 2': roundNumber(deaeratorProps[1]),
                    'Параметр 3': roundNumber(deaeratorProps[2]),
                    'Параметр 4': roundNumber(deaeratorProps[3]),
                    // ... добавь еще, если их больше 4, или сделай динамически
                }];
                const deaeratorWs = XLSX.utils.json_to_sheet(deaeratorSheetData);
                XLSX.utils.book_append_sheet(wb, deaeratorWs, 'Параметры деаэратора');
            }

            XLSX.writeFile(wb, `Расчет_${stockId || 'клапана'}.xlsx`);
            toast({title: "Excel файл успешно создан!", status: "success", duration: 3000, isClosable: true});
        } catch (e) {
            console.error("Ошибка при создании Excel:", e);
            toast({
                title: "Ошибка при создании Excel",
                description: String(e),
                status: "error",
                duration: 5000,
                isClosable: true
            });
        }
    };

    // Кнопка "Сохранить в базе данных" теперь просто показывает сообщение,
    // так как реальное сохранение происходит при вызове /calculate
    const handleShowSavedMessage = () => {
        setIsSavedMessageVisible(true);
        // Можно добавить таймаут, чтобы сообщение исчезло
        setTimeout(() => setIsSavedMessageVisible(false), 4000);
    };

    return (
        <VStack spacing={6} p={5} align="stretch" w="100%" maxW="container.xl" mx="auto"> {/* Увеличил maxW */}
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
                {Object.keys(inputData).length > 0 ? (
                    <SimpleGrid columns={{base: 1, md: 2}} spacing={3}>
                        {inputDataEntries.map(entry => (
                            entry.value !== undefined && entry.value !== null && entry.value !== '' &&
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
                                    {Object.keys(ejectorProps[0] || {}).map(key => <Th
                                        key={`th-ejector-${key}`}>{key.toUpperCase()}</Th>)}
                                </Tr>
                            </Thead>
                            <Tbody>
                                {ejectorProps.map((prop: any, index: number) => (
                                    <Tr key={`ejector-res-${index}`}>
                                        {Object.values(prop).map((val: any, idx) => (
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
                    {/* Отображаем как строку или в несколько колонок, если известно больше о структуре */}
                    <Text borderWidth="1px" borderRadius="md" p={3}>
                        {/* Можно сделать более осмысленное отображение, если известны названия параметров */}
                        {deaeratorProps.map((val, idx) => `Парам. ${idx + 1}: ${roundNumber(val)}`).join('; ')}
                    </Text>
                </Box>
            )}

            <HStack spacing={4} justifyContent="center" mt={8}>
                <Button onClick={handleDownloadExcel} colorScheme="green" variant="solid" size="lg" minW="220px">
                    Сохранить в виде Excel
                </Button>
                {/* Кнопка "Сохранить в базе данных" теперь просто информационная */}
                <Button
                    onClick={handleShowSavedMessage}
                    colorScheme="blue"
                    variant="outline"
                    size="lg"
                    minW="220px"
                    // isDisabled={isSavedMessageVisible} // Можно дизейблить, пока сообщение видно
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