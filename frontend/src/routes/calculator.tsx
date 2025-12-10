import {useState, useCallback, useEffect} from 'react';
import {createFileRoute, useSearch, useNavigate} from '@tanstack/react-router';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {Box, Spinner, Text, VStack, useToast} from '@chakra-ui/react';

import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';
import {type HistoryEntry, LOCAL_STORAGE_HISTORY_KEY} from '../components/Common/Sidebar';

import {
    ResultsService,
    CalculationsService,
    TurbinesService,
    ValvesService,
    ApiError,
    type TurbineInfo,
    type ValveInfo_Output as ValveInfo,
    type CalculationResultDB as ClientCalculationResult,
    type CalculationParams,
} from '../client';

interface ExpectedOutputData {
    Gi?: number[];
    Pi_in?: number[];
    Ti?: number[];
    Hi?: number[];
    deaerator_props?: any[];
    ejector_props?: Array<Record<string, number>>;
}

type CalculatorStep =
    | 'turbineSearch'
    | 'stockSelection'
    | 'loadingPreviousCalculation'
    | 'earlyCalculation'
    | 'stockInput'
    | 'loadingHistoryResult'
    | 'results';

export const Route = createFileRoute('/calculator')({
    component: CalculatorPage,
    validateSearch: (search: Record<string, unknown>) => ({
        resultId: search.resultId ? String(search.resultId) : undefined,
        stockIdToLoad: search.stockIdToLoad ? String(search.stockIdToLoad) : undefined,
        turbineIdToLoad: search.turbineIdToLoad ? String(search.turbineIdToLoad) : undefined,

        // Параметры для интеграции
        taskId: search.taskId ? Number(search.taskId) : undefined,
        embedded: search.embedded === 'true' || search.embedded === true,
    }),
});

export function getApiErrorDetail(error: any): string | undefined {
    if (error instanceof ApiError && error.body && typeof error.body === 'object') {
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
    const searchParams = useSearch({from: Route.fullPath});

    // Флаги интеграции
    const isEmbedded = searchParams.embedded;
    const taskId = searchParams.taskId;

    const [currentStep, setCurrentStep] = useState<CalculatorStep>('turbineSearch');
    const [selectedTurbine, setSelectedTurbine] = useState<TurbineInfo | null>(null);
    const [selectedStock, setSelectedStock] = useState<ValveInfo | null>(null);
    const [calculationData, setCalculationData] = useState<ClientCalculationResult | null>(null);

    // --- Обработка сообщений от Balance+ ---
    useEffect(() => {
        if (!isEmbedded) return;

        const handleMessage = (event: MessageEvent) => {
            const {type, payload} = event.data;

            if (type === 'WSA_RESTORE_STATE') {
                console.log("📥 Stock-Calc: Received state restore request", payload);

                if (payload && payload.input && payload.output) {
                    // Формируем объект результата из полученных данных
                    const restoredData: ClientCalculationResult = {
                        id: 0,
                        input_data: payload.input,
                        output_data: payload.output,
                        stock_name: payload.input.valve_drawing || 'Unknown',
                        turbine_name: payload.input.turbine_name || 'Unknown',
                        calc_timestamp: new Date().toISOString(),
                        user_name: 'System',
                    };

                    setCalculationData(restoredData);

                    // Если есть имена, можно попробовать установить их в стейт (визуально)
                    // Но для ResultsPage важнее сам calculationData
                    if (payload.input.turbine_name) {
                        setSelectedTurbine({id: 0, name: payload.input.turbine_name} as any);
                    }
                    if (payload.input.valve_drawing) {
                        setSelectedStock({id: 0, name: payload.input.valve_drawing} as any);
                    }

                    // Переходим сразу к результатам
                    setCurrentStep('results');

                    toast({
                        title: "Данные восстановлены",
                        description: "Загружен предыдущий расчет из задачи.",
                        status: "info",
                        duration: 3000,
                        position: "top"
                    });
                }
            }
        };

        window.addEventListener('message', handleMessage);

        const timer = setTimeout(() => {
            console.log("📤 Stock-Calc: Sending WSA_READY");
            window.parent.postMessage({type: 'WSA_READY'}, '*');
        }, 500);

        return () => {
            window.removeEventListener('message', handleMessage);
            clearTimeout(timer);
        };
    }, [isEmbedded, toast]);

    const isLoadingFromHistory = !!searchParams.resultId;

    const {
        data: loadedResultDataFromHistory,
        isLoading: isLoadingResultFromHistory,
        isError: isErrorResultFromHistory,
        error: errorResultFromHistory,
    } = useQuery({
        queryKey: ['calculationResultById', searchParams.resultId],
        queryFn: async () => {
            if (!searchParams.resultId) throw new Error("ID результата не предоставлен");
            const id = parseInt(searchParams.resultId, 10);
            if (isNaN(id)) throw new Error("Неверный ID результата");
            const result = await ResultsService.resultsReadCalculationResult({resultId: id});
            return {
                ...result,
                input_data: typeof result.input_data === 'string' ? JSON.parse(result.input_data) : result.input_data,
                output_data: typeof result.output_data === 'string' ? JSON.parse(result.output_data) : result.output_data,
            };
        },
        enabled: !!searchParams.resultId,
        retry: 1,
    });

    const {
        data: loadedTurbineFromHistory,
        isLoading: isLoadingTurbineFromHistory,
        isError: isErrorTurbineFromHistory,
        error: errorTurbineFromHistory,
    } = useQuery({
        queryKey: ['turbineByIdForHistory', searchParams.turbineIdToLoad],
        queryFn: async () => {
            if (!searchParams.turbineIdToLoad) throw new Error("ID турбины не предоставлен");
            const id = parseInt(searchParams.turbineIdToLoad, 10);
            if (isNaN(id)) throw new Error("Неверный ID турбины");
            return TurbinesService.turbinesReadTurbineById({turbineId: id});
        },
        enabled: !!searchParams.turbineIdToLoad && !!searchParams.resultId,
        retry: 1,
    });

    const {
        data: loadedStockFromHistory,
        isLoading: isLoadingStockFromHistory,
        isError: isErrorStockFromHistory,
        error: errorStockFromHistory,
    } = useQuery({
        queryKey: ['stockByIdForHistory', searchParams.stockIdToLoad],
        queryFn: async () => {
            if (!searchParams.stockIdToLoad) throw new Error("ID штока не предоставлен");
            const id = parseInt(searchParams.stockIdToLoad, 10);
            if (isNaN(id)) throw new Error("Неверный ID штока");
            return ValvesService.valvesReadValveById({valveId: id});
        },
        enabled: !!searchParams.stockIdToLoad && !!searchParams.resultId,
        retry: 1,
    });

    const {
        data: latestPreviousResultData,
        isLoading: isLoadingLatestPrevious,
        isError: isErrorLatestPrevious,
        error: errorLatestPrevious,
    } = useQuery({
        queryKey: ['valveResults', selectedStock?.name],
        queryFn: async () => {
            if (!selectedStock?.name) return [];
            const encodedStockName = encodeURIComponent(selectedStock.name);
            const results = await ResultsService.resultsGetCalculationResults({valveName: encodedStockName});
            return results.map(r => ({
                ...r,
                input_data: typeof r.input_data === 'string' ? JSON.parse(r.input_data) : r.input_data,
                output_data: typeof r.output_data === 'string' ? JSON.parse(r.output_data) : r.output_data,
            }));
        },
        enabled: !!selectedStock?.name && !isLoadingFromHistory,
        select: (data) => (data && data.length > 0 ? data[0] : null),
        retry: (failureCount, error) => (error as ApiError)?.status !== 404 && failureCount < 1,
    });

    useEffect(() => {
        if (!searchParams.resultId) {
            if (currentStep === 'loadingHistoryResult') {
                setCurrentStep('turbineSearch');
            }
            return;
        }

        if (isLoadingResultFromHistory
            || (searchParams.turbineIdToLoad && isLoadingTurbineFromHistory)
            || (searchParams.stockIdToLoad && isLoadingStockFromHistory)) {
            if (currentStep !== 'loadingHistoryResult') {
                setCurrentStep('loadingHistoryResult');
            }
            return;
        }

        let shouldClearUrlParams = false;
        if (currentStep === 'loadingHistoryResult' || searchParams.resultId) {
            shouldClearUrlParams = true;
        }

        if (isErrorResultFromHistory || !loadedResultDataFromHistory) {
            toast({
                title: "Ошибка загрузки данных расчета из истории",
                description: getApiErrorDetail(errorResultFromHistory) || (errorResultFromHistory as Error)?.message,
                status: "error"
            });
            setCurrentStep('turbineSearch');
        } else {
            setCalculationData(loadedResultDataFromHistory);
            setSelectedTurbine(loadedTurbineFromHistory || null);
            setSelectedStock(loadedStockFromHistory || null);
            setCurrentStep('results');
            toast({title: `Расчет "${loadedResultDataFromHistory.stock_name}" загружен из истории`, status: "success"});

            if (searchParams.turbineIdToLoad && (isErrorTurbineFromHistory || !loadedTurbineFromHistory)) {
                toast({
                    title: "Предупреждение: не удалось загрузить данные турбины из истории.",
                    description: getApiErrorDetail(errorTurbineFromHistory) || (errorTurbineFromHistory as Error)?.message,
                    status: "warning"
                });
            }
            if (searchParams.stockIdToLoad && (isErrorStockFromHistory || !loadedStockFromHistory)) {
                toast({
                    title: "Предупреждение: не удалось загрузить данные штока из истории.",
                    description: getApiErrorDetail(errorStockFromHistory) || (errorStockFromHistory as Error)?.message,
                    status: "warning"
                });
            }
        }

        if (shouldClearUrlParams) {
            navigate({
                search: (prev: any) => ({
                    ...prev,
                    resultId: undefined,
                    stockIdToLoad: undefined,
                    turbineIdToLoad: undefined
                }),
                replace: true
            });
        }

    }, [
        searchParams.resultId, searchParams.turbineIdToLoad, searchParams.stockIdToLoad,
        loadedResultDataFromHistory, isLoadingResultFromHistory, isErrorResultFromHistory, errorResultFromHistory,
        loadedTurbineFromHistory, isLoadingTurbineFromHistory, isErrorTurbineFromHistory, errorTurbineFromHistory,
        loadedStockFromHistory, isLoadingStockFromHistory, isErrorStockFromHistory, errorStockFromHistory,
        navigate, toast, currentStep
    ]);

    useEffect(() => {
        if (!selectedStock || searchParams.resultId || calculationData || currentStep === 'loadingHistoryResult') {
            return;
        }

        if (isLoadingLatestPrevious) {
            if (currentStep !== 'loadingPreviousCalculation') setCurrentStep('loadingPreviousCalculation');
            return;
        }

        if (currentStep === 'loadingPreviousCalculation' && selectedStock) {
            if (isErrorLatestPrevious) {
                if (errorLatestPrevious instanceof ApiError && errorLatestPrevious.status === 404) {
                    console.log('No previous calculations found for stock:', selectedStock.name);
                    setCalculationData(null);
                    setCurrentStep('stockInput');
                } else {
                    let errorMessage = "Не удалось получить данные.";
                    if (errorLatestPrevious) {
                        const detail = getApiErrorDetail(errorLatestPrevious);
                        errorMessage = detail || (errorLatestPrevious as Error)?.message || errorMessage;
                    }
                    toast({
                        title: "Ошибка загрузки предыдущих расчетов",
                        description: errorMessage,
                        status: "error"
                    });
                    setCalculationData(null);
                    setCurrentStep('stockInput');
                }
            } else if (latestPreviousResultData) {
                console.log('Found previous calculation:', latestPreviousResultData);
                setCalculationData(latestPreviousResultData);
                setCurrentStep('earlyCalculation');
            } else {
                console.log('No previous calculations found');
                setCalculationData(null);
                setCurrentStep('stockInput');
            }
        }
    }, [
        latestPreviousResultData, isLoadingLatestPrevious, isErrorLatestPrevious, errorLatestPrevious,
        selectedStock, toast, searchParams.resultId, calculationData, currentStep
    ]);

    const handleStockSelect = useCallback((stock: ValveInfo) => {
        console.log('Stock selected:', stock);

        navigate({
            search: (p: any) => ({
                ...p,
                resultId: undefined,
                stockIdToLoad: undefined,
                turbineIdToLoad: undefined
            }), replace: true
        });

        setSelectedStock(stock);
        setCalculationData(null);
        queryClient.invalidateQueries({queryKey: ['valveResults', stock.id]});
        setCurrentStep('loadingPreviousCalculation');
    }, [navigate, queryClient]);

    const calculationMutation = useMutation<ClientCalculationResult, ApiError, CalculationParams>({
        mutationFn: (params: CalculationParams) => CalculationsService.calculationsCalculate({requestBody: params}),
        onSuccess: (data) => {
            const parsedData = {
                ...data,
                input_data: typeof data.input_data === 'string' ? JSON.parse(data.input_data) : data.input_data,
                output_data: typeof data.output_data === 'string' ? JSON.parse(data.output_data) : data.output_data,
            };
            setCalculationData(parsedData);
            setCurrentStep('results');
            toast({title: "Расчет выполнен успешно!", status: "success"});

            if (selectedStock?.id !== undefined && selectedTurbine?.id !== undefined && parsedData.id !== undefined) {
                const newHistoryEntry: HistoryEntry = {
                    id: String(parsedData.id),
                    stockName: selectedStock.name,
                    stockId: selectedStock.id,
                    turbineName: selectedTurbine.name,
                    turbineId: selectedTurbine.id,
                    timestamp: Date.now(),
                };
                const storedHistory = localStorage.getItem(LOCAL_STORAGE_HISTORY_KEY);
                let currentHistory: HistoryEntry[] = [];
                if (storedHistory) {
                    try {
                        currentHistory = JSON.parse(storedHistory);
                    } catch (e) {
                        console.error(e);
                    }
                }
                const updatedHistory = [newHistoryEntry, ...currentHistory].slice(0, 20);
                localStorage.setItem(LOCAL_STORAGE_HISTORY_KEY, JSON.stringify(updatedHistory));
                window.dispatchEvent(new Event('wsaHistoryUpdated'));
            }

            if (selectedStock?.id) {
                void queryClient.invalidateQueries({queryKey: ['valveResults', selectedStock.id]});
            }
        },
        onError: (error: ApiError) => {
            const detail = getApiErrorDetail(error);
            toast({
                title: "Ошибка при выполнении расчета",
                description: detail || error.message,
                status: "error"
            });
        },
    });

    const handleTurbineSelect = useCallback((turbine: TurbineInfo) => {
        navigate({
            search: (p: any) => ({
                ...p,
                resultId: undefined,
                stockIdToLoad: undefined,
                turbineIdToLoad: undefined
            }), replace: true
        });
        setSelectedTurbine(turbine);
        setSelectedStock(null);
        setCalculationData(null);
        setCurrentStep('stockSelection');
    }, [navigate]);

    const handleRecalculateDecision = useCallback((recalculate: boolean) => {
        if (!recalculate && calculationData) {
            setCurrentStep('results');
        } else {
            setCurrentStep('stockInput');
        }
    }, [calculationData]);

    const handleStockInputSubmit = useCallback((inputData: CalculationParams) => {
        if (!selectedTurbine?.id || !selectedStock?.id) {
            toast({title: "Ошибка", description: "Турбина или шток не выбраны для расчета.", status: "error"});
            setCurrentStep('turbineSearch');
            return;
        }
        const paramsForApi: CalculationParams = {
            ...inputData,
            turbine_name: selectedTurbine.name,
            valve_drawing: selectedStock.name,
            valve_id: selectedStock.id,
        };
        calculationMutation.mutate(paramsForApi);
    }, [calculationMutation, selectedTurbine, selectedStock, toast]);

    const handleGoBackToTurbineSearch = useCallback(() => {
        navigate({
            search: (p: any) => ({
                ...p,
                resultId: undefined,
                stockIdToLoad: undefined,
                turbineIdToLoad: undefined
            }), replace: true
        });
        setSelectedTurbine(null);
        setSelectedStock(null);
        setCalculationData(null);
        setCurrentStep('turbineSearch');
    }, [navigate]);

    const handleGoBackToStockSelection = useCallback(() => {
        navigate({
            search: (p: any) => ({
                ...p,
                resultId: undefined,
                stockIdToLoad: undefined,
                turbineIdToLoad: undefined
            }), replace: true
        });
        setSelectedStock(null);
        setCalculationData(null);
        setCurrentStep('stockSelection');
    }, [navigate, selectedTurbine]);

    const renderContent = () => {
        if (currentStep === 'loadingHistoryResult' || calculationMutation.isPending
            || (isLoadingResultFromHistory && searchParams.resultId)
            || (isLoadingTurbineFromHistory && searchParams.turbineIdToLoad)
            || (isLoadingStockFromHistory && searchParams.stockIdToLoad)) {
            let loadingText = "Загрузка данных...";
            if (currentStep === 'loadingHistoryResult') loadingText = "Загрузка из истории...";
            if (calculationMutation.isPending) loadingText = "Выполняется расчет...";
            return (
                <VStack spacing={4} align="center" justify="center" minH="calc(100vh - 200px)">
                    <Spinner size="xl" color="teal.500"/>
                    <Text>{loadingText}</Text>
                </VStack>
            );
        }

        if (currentStep === 'loadingPreviousCalculation') {
            return (
                <VStack spacing={4} align="center" justify="center" minH="calc(100vh - 200px)">
                    <Spinner size="xl" color="teal.500"/>
                    <Text>Поиск предыдущих расчетов...</Text>
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
                    return <EarlyCalculationPage
                        stockId={selectedStock?.name || calculationData.stock_name || 'N/A'}
                        lastCalculation={calculationData}
                        onRecalculate={handleRecalculateDecision}
                        onGoBack={handleGoBackToStockSelection}
                    />;
                }
                console.warn("EarlyCalculation: calculationData is null, going to stockInput");
                setCurrentStep('stockInput');
                return null;
            case 'stockInput':
                if (selectedStock && selectedTurbine) {
                    return <StockInputPage
                        stock={selectedStock}
                        turbine={selectedTurbine}
                        onSubmit={handleStockInputSubmit}
                        initialData={calculationData?.input_data as Partial<CalculationParams> | undefined}
                        onGoBack={handleGoBackToStockSelection}
                    />;
                }
                setCurrentStep('turbineSearch');
                return null;
            case 'results':
                if (calculationData) {
                    return <ResultsPage
                        stockId={calculationData.stock_name}
                        stockInfo={selectedStock}
                        calculationId={calculationData.id}
                        inputData={calculationData.input_data as CalculationParams}
                        outputData={calculationData.output_data as ExpectedOutputData}
                        isEmbedded={isEmbedded}
                        taskId={taskId}
                        onGoBack={() => {
                            if (isEmbedded) {
                                setCalculationData(null);
                                setCurrentStep('turbineSearch');
                            } else {
                                setCalculationData(null);
                                if (selectedStock && selectedTurbine) {
                                    setCurrentStep('stockInput');
                                } else if (selectedTurbine) {
                                    setCurrentStep('stockSelection');
                                } else {
                                    setCurrentStep('turbineSearch');
                                }
                            }
                        }}
                    />;
                }
                setCurrentStep('turbineSearch');
                return null;
            default:
                if (currentStep !== 'turbineSearch') setCurrentStep('turbineSearch');
                return null;
        }
    };

    return (
        <Box w="100%">
            <Box display="flex" justifyContent="center" alignItems="flex-start" minH="calc(100vh - 150px)">
                {renderContent()}
            </Box>
        </Box>
    );
}