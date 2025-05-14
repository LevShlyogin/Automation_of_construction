import {useState, useCallback, useEffect} from 'react';
import {createFileRoute} from '@tanstack/react-router';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {Box, Spinner, Text, VStack, useToast} from '@chakra-ui/react';

import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';

import {
    ResultsService,
    CalculationsService,
    ApiError,
    type TurbineInfo,
    type ValveInfo_Output as ValveInfo,
    type CalculationResultDB as ClientCalculationResult,
    type CalculationParams,
} from '../client';

type CalculatorStep =
    | 'turbineSearch'
    | 'stockSelection'
    | 'earlyCalculation'
    | 'stockInput'
    | 'results';

type CalculationDataType = ClientCalculationResult;

export const Route = createFileRoute('/calculator')({
    component: CalculatorPage,
});

function CalculatorPage() {
    const queryClient = useQueryClient();
    const toast = useToast();

    const [currentStep, setCurrentStep] = useState<CalculatorStep>('turbineSearch');
    const [selectedTurbine, setSelectedTurbine] = useState<TurbineInfo | null>(null);
    const [selectedStock, setSelectedStock] = useState<ValveInfo | null>(null);
    const [calculationData, setCalculationData] = useState<CalculationDataType | null>(null);

    const {
        data: latestPreviousResult,
        isLoading: isLoadingPreviousResults,
        isError: isErrorPreviousResults,
        error: errorPreviousResults,
    } = useQuery<ClientCalculationResult[], ApiError, CalculationDataType | null, [string, string | null | undefined]>({
        queryKey: ['valveResults', selectedStock?.name],
        queryFn: async () => {
            if (!selectedStock?.name) return [];
            const results = await ResultsService.resultsGetCalculationResults({valveName: selectedStock.name});
            return results.map(r => ({
                ...r,
                input_data: typeof r.input_data === 'string' ? JSON.parse(r.input_data) : r.input_data,
                output_data: typeof r.output_data === 'string' ? JSON.parse(r.output_data) : r.output_data,
            }));
        },
        enabled: !!selectedStock?.name,
        select: (data) => (data && data.length > 0 ? data[0] : null),
    });

    useEffect(() => {
        if (!selectedStock) return;

        if (isLoadingPreviousResults) return;

        if (isErrorPreviousResults) {
            let errorMessage = "Не удалось получить данные.";
            if (errorPreviousResults) {
                if (errorPreviousResults instanceof ApiError && errorPreviousResults.body && typeof errorPreviousResults.body === 'object') {
                    const detail = (errorPreviousResults.body as any).detail;
                    if (typeof detail === 'string') {
                        errorMessage = detail;
                    } else if ((errorPreviousResults as Error).message) {
                        errorMessage = (errorPreviousResults as Error).message;
                    }
                } else if ((errorPreviousResults as Error).message) {
                    errorMessage = (errorPreviousResults as Error).message;
                }
            }
            toast({
                title: "Ошибка загрузки предыдущих расчетов",
                description: errorMessage,
                status: "error",
                duration: 5000,
                isClosable: true,
            });
            setCalculationData(null);
            setCurrentStep('stockInput');
            return;
        }

        if (latestPreviousResult) {
            setCalculationData(latestPreviousResult);
            setCurrentStep('earlyCalculation');
        } else {
            setCalculationData(null);
            setCurrentStep('stockInput');
        }
    }, [latestPreviousResult, isLoadingPreviousResults, isErrorPreviousResults, errorPreviousResults, selectedStock, toast]);


    const calculationMutation = useMutation<ClientCalculationResult, ApiError, CalculationParams>({
        mutationFn: (params: CalculationParams) => {
            return CalculationsService.calculationsCalculate({requestBody: params});
        },
        onSuccess: (data) => {
            const parsedData = {
                ...data,
                input_data: typeof data.input_data === 'string' ? JSON.parse(data.input_data) : data.input_data,
                output_data: typeof data.output_data === 'string' ? JSON.parse(data.output_data) : data.output_data,
            };
            setCalculationData(parsedData);
            setCurrentStep('results');
            toast({
                title: "Расчет выполнен успешно!",
                status: "success",
                duration: 3000,
                isClosable: true,
            });
            if (selectedStock?.name) {
                void queryClient.invalidateQueries({queryKey: ['valveResults', selectedStock.name]});
            }
        },
        onError: (error: ApiError) => {
            let errorMessage = "Произошла неизвестная ошибка.";
            if (error.body && typeof error.body === 'object') {
                const detail = (error.body as any).detail;
                if (typeof detail === 'string') {
                    errorMessage = detail;
                } else if (error.message) {
                    errorMessage = error.message;
                }
            } else if (error.message) {
                errorMessage = error.message;
            }
            toast({
                title: "Ошибка при выполнении расчета",
                description: errorMessage,
                status: "error",
                duration: 5000,
                isClosable: true,
            });
        },
    });

    const handleTurbineSelect = useCallback((turbine: TurbineInfo) => {
        setSelectedTurbine(turbine);
        setSelectedStock(null);
        setCalculationData(null);
        setCurrentStep('stockSelection');
    }, []);

    const handleStockSelect = useCallback((stock: ValveInfo) => {
        if (selectedStock?.id === stock.id) {
        } else {
            setSelectedStock(stock);
            setCalculationData(null);
        }
    }, [selectedStock]);

    const handleRecalculateDecision = useCallback((recalculate: boolean) => {
        if (!recalculate && calculationData) {
            setCurrentStep('results');
        } else {
            setCalculationData(null);
            setCurrentStep('stockInput');
        }
    }, [calculationData]);

    const handleStockInputSubmit = useCallback((inputData: CalculationParams) => {
        const paramsForApi: CalculationParams = {
            ...inputData,
            turbine_name: selectedTurbine?.name || inputData.turbine_name,
            valve_drawing: selectedStock?.name || inputData.valve_drawing,
            valve_id: selectedStock?.id || inputData.valve_id,
        };
        calculationMutation.mutate(paramsForApi);
    }, [calculationMutation, selectedTurbine, selectedStock]);

    const handleGoBackToTurbineSearch = useCallback(() => {
        setSelectedTurbine(null);
        setSelectedStock(null);
        setCalculationData(null);
        setCurrentStep('turbineSearch');
    }, []);

    const renderContent = () => {
        if (calculationMutation.isPending) {
            return (
                <VStack spacing={4} align="center" justify="center" minH="300px">
                    <Spinner size="xl" color="teal.500"/>
                    <Text>Выполняется расчет...</Text>
                </VStack>
            );
        }
        if (currentStep !== 'turbineSearch' && isLoadingPreviousResults && selectedStock && !latestPreviousResult && !isErrorPreviousResults) {
            return (
                <VStack spacing={4} align="center" justify="center" minH="300px">
                    <Spinner size="xl" color="teal.500"/>
                    <Text>Загрузка данных о клапане...</Text>
                </VStack>
            );
        }

        switch (currentStep) {
            case 'turbineSearch':
                return <TurbineSearch onSelectTurbine={handleTurbineSelect}/>;
            case 'stockSelection':
                return <StockSelection turbine={selectedTurbine} onSelectValve={handleStockSelect}
                                       onGoBack={handleGoBackToTurbineSearch}/>;
            case 'earlyCalculation':
                if (calculationData) {
                    return (
                        <EarlyCalculationPage
                            stockId={selectedStock?.name || 'N/A'}
                            lastCalculation={calculationData}
                            onRecalculate={handleRecalculateDecision}
                        />
                    );
                }
                setCurrentStep('stockInput');
                return null;
            case 'stockInput':
                if (selectedStock && selectedTurbine) {
                    return (
                        <StockInputPage
                            stock={selectedStock}
                            turbine={selectedTurbine}
                            onSubmit={handleStockInputSubmit}
                            initialData={calculationData?.input_data}
                        />
                    );
                }
                setCurrentStep('turbineSearch');
                return null;
            case 'results':
                if (calculationData && selectedStock) {
                    return (
                        <ResultsPage
                            stockId={selectedStock.name}
                            inputData={calculationData.input_data}
                            outputData={calculationData.output_data}
                        />
                    );
                }
                setCurrentStep('turbineSearch');
                return null;
            default:
                setCurrentStep('turbineSearch');
                return null;
        }
    };

    return (
        <Box w="100%"> {}
            <Box display="flex" justifyContent="center" alignItems="flex-start">
                {renderContent()}
            </Box>
        </Box>
    );
}