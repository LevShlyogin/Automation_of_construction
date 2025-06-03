import {useState, useCallback, useEffect} from 'react';
import {createFileRoute, useSearch, useNavigate} from '@tanstack/react-router';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {Box, Spinner, Text, VStack, useToast} from '@chakra-ui/react';

import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';
import {type HistoryEntry} from '../components/Common/Sidebar';

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
const LOCAL_STORAGE_HISTORY_KEY = 'wsaCalculatorHistory';


export const Route = createFileRoute('/calculator')({
    component: CalculatorPage,
    validateSearch: (search: Record<string, unknown>) => {
        return {
            loadFromResultId: search.loadFromResultId ? String(search.loadFromResultId) : undefined,
        };
    },
});

function getApiErrorDetail(error: any): string | undefined {
    if (error instanceof ApiError && error.body && typeof error.body === 'object') {
        // Проверяем, является ли body объектом и имеет ли он свойство detail типа string
        if ('detail' in error.body && typeof (error.body as any).detail === 'string') {
            return (error.body as any).detail;
        }
    }
    return undefined;
}

function CalculatorPage() {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const toast = useToast();

    const {loadFromResultId} = useSearch({from: Route.fullPath});

    const [currentStep, setCurrentStep] = useState<CalculatorStep>('turbineSearch');
    const [selectedTurbine, setSelectedTurbine] = useState<TurbineInfo | null>(null);
    const [selectedStock, setSelectedStock] = useState<ValveInfo | null>(null);
    const [calculationData, setCalculationData] = useState<ClientCalculationResult | null>(null);

    const {
        data: loadedResultFromHistory,
        isLoading: isLoadingResultFromHistory,
        isError: isErrorResultFromHistory,
        error: errorResultFromHistory,
    } = useQuery<ClientCalculationResult, ApiError, ClientCalculationResult, [string, string | undefined]>({
        queryKey: ['calculationResultById', loadFromResultId],
        queryFn: async () => {
            if (!loadFromResultId) throw new Error("ID результата не предоставлен");
            const resultId = parseInt(loadFromResultId, 10);
            if (isNaN(resultId)) throw new Error("Неверный ID результата");

            const result = await ResultsService.resultsReadCalculationResult({resultId});
            return {
                ...result,
                input_data: result.input_data,
                output_data: result.output_data,
            };
        },
        enabled: !!loadFromResultId,
        retry: false,
    });

    useEffect(() => {
        const historyIdToLoad = loadFromResultId;

        if (historyIdToLoad && !isLoadingResultFromHistory && !isErrorResultFromHistory) { // Добавили проверки на загрузку/ошибку
            if (loadedResultFromHistory) {
                setCalculationData(loadedResultFromHistory);
                const inputParams = loadedResultFromHistory.input_data as Partial<CalculationParams>;
                if (inputParams?.turbine_name) {
                    setSelectedTurbine({name: inputParams.turbine_name, id: 0} as TurbineInfo); // ЗАГЛУШКА ID и типа
                }
                if (inputParams?.valve_drawing && inputParams?.valve_id !== undefined) {
                    setSelectedStock({name: inputParams.valve_drawing, id: inputParams.valve_id} as ValveInfo); // ЗАГЛУШКА для остальных полей
                }

                setCurrentStep('results');
                toast({
                    title: `Расчет "${loadedResultFromHistory.stock_name}" загружен из истории`,
                    status: "success",
                    duration: 3000
                });
            } else if (!isLoadingResultFromHistory) {
                toast({title: "Не удалось загрузить расчет из истории.", status: "warning"});
            }
            navigate({search: (prev: any) => ({...prev, loadFromResultId: undefined}), replace: true}).then();
        } else if (historyIdToLoad && isErrorResultFromHistory && !isLoadingResultFromHistory) {
            toast({
                title: "Ошибка загрузки расчета из истории",
                description: getApiErrorDetail(errorResultFromHistory)
                    || (errorResultFromHistory as Error)?.message || "Не удалось получить данные.",
                status: "error",
                duration: 5000,
                isClosable: true,
            });
            navigate({search: (prev: any) => ({...prev, loadFromResultId: undefined}), replace: true}).then();
        }
    }, [
        loadFromResultId,
        loadedResultFromHistory,
        isLoadingResultFromHistory,
        isErrorResultFromHistory,
        errorResultFromHistory,
        navigate,
        toast
    ]);

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
                input_data: r.input_data,
                output_data: r.output_data,
            }));
        },
        enabled: !!selectedStock?.name && !loadFromResultId,
        select: (data) => (data && data.length > 0 ? data[0] : null),
    });

    useEffect(() => {
        if (!selectedStock || loadFromResultId) return;

        if (isLoadingPreviousResults) return;

        if (isErrorPreviousResults) {
            let errorMessage = "Не удалось получить данные.";
            if (errorPreviousResults) {
                if (errorPreviousResults.body && typeof errorPreviousResults.body === 'object') {
                    const detail = getApiErrorDetail(errorPreviousResults);
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
    }, [latestPreviousResult, isLoadingPreviousResults, isErrorPreviousResults,
        errorPreviousResults, selectedStock, toast, loadFromResultId]);


    const calculationMutation = useMutation<ClientCalculationResult, ApiError, CalculationParams>({
        mutationFn: (params: CalculationParams) => {
            return CalculationsService.calculationsCalculate({requestBody: params});
        },
        onSuccess: (data) => {
            const parsedData = {
                ...data,
                input_data: data.input_data,
                output_data: data.output_data,
            };
            setCalculationData(parsedData);
            setCurrentStep('results');
            toast({
                title: "Расчет выполнен успешно!",
                status: "success",
                duration: 3000,
                isClosable: true,
            });

            if (selectedStock && selectedTurbine && data.id) {

                const newHistoryEntry: HistoryEntry = {
                    id: String(data.id),
                    stockName: selectedStock.name,
                    turbineName: selectedTurbine.name,
                    timestamp: Date.now(),
                };

                const storedHistory = localStorage.getItem(LOCAL_STORAGE_HISTORY_KEY);
                let currentHistory: HistoryEntry[] = [];
                if (storedHistory) {
                    try {
                        currentHistory = JSON.parse(storedHistory);
                    } catch (e) {
                        console.error("Failed to parse history for saving", e);
                    }
                }
                const updatedHistory = [newHistoryEntry, ...currentHistory].slice(0, 20);
                localStorage.setItem(LOCAL_STORAGE_HISTORY_KEY, JSON.stringify(updatedHistory));

                window.dispatchEvent(new Event('wsaHistoryUpdated'));
            }

            if (selectedStock?.name) {
                void queryClient.invalidateQueries({queryKey: ['valveResults', selectedStock.name]});
            }
        },
        onError: (error: ApiError) => {
            const detail = getApiErrorDetail(error);
            toast({
                title: "Ошибка при выполнении расчета",
                description: detail || error.message || "Произошла неизвестная ошибка.",
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
        if (selectedStock?.id === stock.id && !isLoadingPreviousResults && !isErrorPreviousResults) {
            if (latestPreviousResult) {
                setCalculationData(latestPreviousResult);
                setCurrentStep('earlyCalculation');
            } else {
                setCalculationData(null);
                setCurrentStep('stockInput');
            }
        } else {
            setSelectedStock(stock);
            setCalculationData(null);
        }
    }, [selectedStock, latestPreviousResult, isLoadingPreviousResults, isErrorPreviousResults]);

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

    const handleGoBackToStockSelection = useCallback(() => {
        setSelectedStock(null);
        setCalculationData(null);
        setCurrentStep('stockSelection');
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

        if (currentStep !== 'turbineSearch' && isLoadingPreviousResults && selectedStock && !latestPreviousResult && !isErrorPreviousResults && !loadFromResultId) {
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
                return <StockSelection
                    turbine={selectedTurbine}
                    onSelectValve={handleStockSelect}
                    onGoBack={handleGoBackToTurbineSearch}
                />;
            case 'earlyCalculation':
                if (calculationData) {
                    return (
                        <EarlyCalculationPage
                            stockId={selectedStock?.name || 'N/A'}
                            lastCalculation={calculationData}
                            onRecalculate={handleRecalculateDecision}
                            onGoBack={handleGoBackToStockSelection}
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
                            onGoBack={handleGoBackToStockSelection}
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
                            inputData={calculationData.input_data as CalculationParams}
                            outputData={calculationData.output_data as any}
                            onGoBack={() => setCurrentStep('stockInput')}
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
        <Box w="100%">
            <Box display="flex" justifyContent="center" alignItems="flex-start">
                {renderContent()}
            </Box>
        </Box>
    );
}