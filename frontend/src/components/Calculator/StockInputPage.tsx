import React, {useEffect} from 'react';
import {useForm, useFieldArray, Controller, type SubmitHandler} from 'react-hook-form';
import {
    Box,
    Button,
    FormControl,
    FormLabel,
    FormErrorMessage,
    NumberInput,
    NumberInputField,
    NumberInputStepper,
    NumberIncrementStepper,
    NumberDecrementStepper,
    Select,
    VStack,
    HStack,
    Heading,
    Text,
    Icon,
} from '@chakra-ui/react';

import {
    type ValveInfo_Output as ValveInfo,
    type TurbineInfo,
    type CalculationParams
} from '../../client';
import {FiChevronLeft} from "react-icons/fi";

interface FormInputValues {
    turbine_name: string;
    valve_drawing: string;
    valve_id: number;
    temperature_start: number | '';
    t_air: number | '';
    count_valves: number;
    p_values: { value: number | '' }[];
    p_ejector: { value: number | '' }[];
    count_parts_select: number;
}

type Props = {
    stock: ValveInfo;
    turbine: TurbineInfo;
    onSubmit: (data: CalculationParams) => void;
    initialData?: Partial<CalculationParams>;
    onGoBack?: () => void;
};

const StockInputPage: React.FC<Props> = ({stock, turbine, onSubmit, initialData, onGoBack}) => {
    const defaultCountParts = initialData?.p_values?.length || stock.count_parts || 2;

    const {
        register,
        handleSubmit,
        control,
        watch,
        reset,
        formState: {errors, isSubmitting},
    } = useForm<FormInputValues>({
        defaultValues: {
            turbine_name: initialData?.turbine_name || turbine.name,
            valve_drawing: initialData?.valve_drawing || stock.name,
            valve_id: initialData?.valve_id || stock.id,
            temperature_start: initialData?.temperature_start ?? '',
            t_air: initialData?.t_air ?? '',
            count_valves: initialData?.count_valves || 3,
            count_parts_select: defaultCountParts,
            p_values: initialData?.p_values?.map(v => ({value: v ?? ''})) || Array(defaultCountParts).fill({value: ''}),
            p_ejector: initialData?.p_ejector?.map(v => ({value: v ?? ''})) || Array(defaultCountParts).fill({value: ''}),
        },
        mode: 'onBlur',
    });

    const watchedCountParts = watch('count_parts_select', defaultCountParts);

    const {fields: pValueFields, append: appendPValue, remove: removePValue} = useFieldArray({
        control,
        name: 'p_values',
    });

    const {fields: pEjectorFields, append: appendPEjector, remove: removePEjector} = useFieldArray({
        control,
        name: 'p_ejector',
    });

    useEffect(() => {
        const currentPValuesLength = pValueFields.length;
        const targetLength = Number(watchedCountParts) || 0;

        if (targetLength > currentPValuesLength) {
            for (let i = 0; i < targetLength - currentPValuesLength; i++) {
                appendPValue({value: ''});
            }
        } else if (targetLength < currentPValuesLength) {
            for (let i = currentPValuesLength - 1; i >= targetLength; i--) {
                removePValue(i);
            }
        }

        const currentPEjectorsLength = pEjectorFields.length;
        if (targetLength > currentPEjectorsLength) {
            for (let i = 0; i < targetLength - currentPEjectorsLength; i++) {
                appendPEjector({value: ''});
            }
        } else if (targetLength < currentPEjectorsLength) {
            for (let i = currentPEjectorsLength - 1; i >= targetLength; i--) {
                removePEjector(i);
            }
        }
    }, [watchedCountParts, appendPValue, removePValue, pValueFields.length, appendPEjector, removePEjector, pEjectorFields.length]);

    useEffect(() => {
        const newDefaultCountParts = initialData?.p_values?.length || stock.count_parts || 2;
        reset({
            turbine_name: initialData?.turbine_name || turbine.name,
            valve_drawing: initialData?.valve_drawing || stock.name,
            valve_id: initialData?.valve_id || stock.id,
            temperature_start: initialData?.temperature_start ?? '',
            t_air: initialData?.t_air ?? '',
            count_valves: initialData?.count_valves || 3,
            count_parts_select: newDefaultCountParts,
            p_values: initialData?.p_values?.map(v => ({value: v ?? ''})) || Array(newDefaultCountParts).fill({value: ''}),
            p_ejector: initialData?.p_ejector?.map(v => ({value: v ?? ''})) || Array(newDefaultCountParts).fill({value: ''}),
        });
    }, [stock, turbine, initialData, reset]);

    const processSubmit: SubmitHandler<FormInputValues> = (data) => {
        const calculationParams: CalculationParams = {
            turbine_name: data.turbine_name,
            valve_drawing: data.valve_drawing,
            valve_id: data.valve_id,
            temperature_start: Number(data.temperature_start),
            t_air: Number(data.t_air),
            count_valves: data.count_valves,
            p_values: data.p_values.map(p => Number(p.value)),
            p_ejector: data.p_ejector.map(p => Number(p.value)),
        };
        onSubmit(calculationParams);
    };

    return (
        <VStack as="form" onSubmit={handleSubmit(processSubmit)} spacing={6} p={5} w="100%" maxW="container.lg"
                mx="auto" align="stretch">
            <Heading as="h2" size="lg" textAlign="center">
                Ввод данных для клапана <Text as="span" color="teal.500">{stock.name}</Text>
            </Heading>
            <Text textAlign="center" fontSize="md" color="gray.600">Турбина: {turbine.name}</Text>

            {onGoBack && (
                <Box width="100%" textAlign="center" my={2}>
                    <Button
                        onClick={onGoBack}
                        variant="outline"
                        colorScheme="teal"
                        size="sm"
                        leftIcon={<Icon as={FiChevronLeft}/>}
                    >
                        Изменить клапан
                    </Button>
                </Box>
            )}

            <input type="hidden" {...register("turbine_name")} />
            <input type="hidden" {...register("valve_drawing")} />
            <input type="hidden" {...register("valve_id")} />

            <FormControl isInvalid={!!errors.count_parts_select}>
                <FormLabel htmlFor="count_parts_select">Количество участков (от 2
                    до {pValueFields.length > 0 ? Math.max(2, pValueFields.length) : 4} ):</FormLabel>
                <Select
                    id="count_parts_select"
                    {...register("count_parts_select", {
                        valueAsNumber: true,
                        onChange: (e) => {
                            const newCount = parseInt(e.target.value, 10);
                            const currentPValuesLength = pValueFields.length;
                            if (newCount > currentPValuesLength) {
                                for (let i = 0; i < newCount - currentPValuesLength; i++) appendPValue({value: ''});
                            } else if (newCount < currentPValuesLength) {
                                for (let i = currentPValuesLength - 1; i >= newCount; i--) removePValue(i);
                            }
                            const currentPEjectorsLength = pEjectorFields.length;
                            if (newCount > currentPEjectorsLength) {
                                for (let i = 0; i < newCount - currentPEjectorsLength; i++) appendPEjector({value: ''});
                            } else if (newCount < currentPEjectorsLength) {
                                for (let i = currentPEjectorsLength - 1; i >= newCount; i--) removePEjector(i);
                            }
                            return newCount;
                        }
                    })}
                    defaultValue={defaultCountParts}
                >
                    {[2, 3, 4].map((value) => (
                        <option key={value} value={value}>
                            {value}
                        </option>
                    ))}
                </Select>
                <FormErrorMessage>{errors.count_parts_select?.message}</FormErrorMessage>
            </FormControl>

            {/* Количество клапанов: Количество клапанов: */}
            <FormControl isRequired isInvalid={!!errors.count_valves}>
                <FormLabel htmlFor="count_valves">Количество клапанов:</FormLabel>
                <Controller
                    name="count_valves"
                    control={control}
                    rules={{required: "Это поле обязательно", min: {value: 1, message: "Минимум 1"}}}
                    render={({field}) => (
                        <NumberInput {...field} min={1}
                                     onChange={(_valueString, valueNumber) => field.onChange(valueNumber)}>
                            <NumberInputField placeholder="Введите количество"/>
                            <NumberInputStepper>
                                <NumberIncrementStepper/>
                                <NumberDecrementStepper/>
                            </NumberInputStepper>
                        </NumberInput>
                    )}
                />
                <FormErrorMessage>{errors.count_valves?.message}</FormErrorMessage>
            </FormControl>

            {/* Входные давления: Введите входные давления: */}
            <Box borderWidth="1px" borderRadius="md" p={4}>
                <Heading as="h3" size="md" mb={3}>Введите входные давления:</Heading>
                <VStack spacing={4} align="stretch">
                    {pValueFields.map((field, index) => (
                        <FormControl key={field.id} isRequired isInvalid={!!errors.p_values?.[index]?.value}>
                            <HStack align="center">
                                <FormLabel htmlFor={`p_values.${index}.value`} mb="0" minW="130px">Давление
                                    P{index + 1}:</FormLabel>
                                <Controller
                                    name={`p_values.${index}.value`}
                                    control={control}
                                    rules={{
                                        required: "Это поле обязательно",
                                        validate: value => value !== '' && !isNaN(parseFloat(value as unknown as string)) || "Должно быть числом"
                                    }}
                                    render={({field: {onChange, onBlur, value, name, ref}}) => (
                                        <NumberInput
                                            value={value === '' ? undefined : Number(value)}
                                            onChange={(_valueAsString, valueAsNumber) => onChange(isNaN(valueAsNumber) ? '' : valueAsNumber)}
                                            onBlur={onBlur}
                                            allowMouseWheel
                                            step={0.001}
                                            precision={3}
                                            min={0}
                                        >
                                            <NumberInputField name={name} ref={ref} placeholder={`P${index + 1}`}/>
                                        </NumberInput>
                                    )}
                                />
                            </HStack>
                            <FormErrorMessage ml="140px">{errors.p_values?.[index]?.value?.message}</FormErrorMessage>
                        </FormControl>
                    ))}
                </VStack>
            </Box>

            {/* Выходные давления: Введите выходные давления: */}
            <Box borderWidth="1px" borderRadius="md" p={4}>
                <Heading as="h3" size="md" mb={3}>Введите выходные давления:</Heading>
                <VStack spacing={4} align="stretch">
                    {pEjectorFields.map((field, index) => (
                        <FormControl key={field.id} isRequired isInvalid={!!errors.p_ejector?.[index]?.value}>
                            <HStack align="center">
                                <FormLabel htmlFor={`p_ejector.${index}.value`} mb="0"
                                           minW="130px">Потребитель {index + 1}:</FormLabel>
                                <Controller
                                    name={`p_ejector.${index}.value`}
                                    control={control}
                                    rules={{
                                        required: "Это поле обязательно",
                                        validate: value => value !== '' && !isNaN(parseFloat(value as unknown as string)) || "Должно быть числом"
                                    }}
                                    render={({field: {onChange, onBlur, value, name, ref}}) => (
                                        <NumberInput
                                            value={value === '' ? undefined : Number(value)}
                                            onChange={(_valueAsString, valueAsNumber) => onChange(isNaN(valueAsNumber) ? '' : valueAsNumber)}
                                            onBlur={onBlur}
                                            allowMouseWheel
                                            step={0.001}
                                            precision={3}
                                            min={0}
                                        >
                                            <NumberInputField name={name} ref={ref}
                                                              placeholder={`Потребитель ${index + 1}`}/>
                                        </NumberInput>
                                    )}
                                />
                            </HStack>
                            <FormErrorMessage ml="140px">{errors.p_ejector?.[index]?.value?.message}</FormErrorMessage>
                        </FormControl>
                    ))}
                </VStack>
            </Box>

            <Box borderWidth="1px" borderRadius="md" p={4}>
                <Heading as="h3" size="md" mb={3}>Введите температурные значения:</Heading>
                <VStack spacing={4} align="stretch">
                    <FormControl isRequired isInvalid={!!errors.temperature_start}>
                        <HStack align="center">
                            <FormLabel htmlFor="temperature_start" mb="0" minW="180px">Начальная температура
                                (°C):</FormLabel>
                            <Controller
                                name="temperature_start"
                                control={control}
                                rules={{
                                    required: "Это поле обязательно",
                                    validate: value => value !== '' && !isNaN(parseFloat(value as unknown as string)) || "Должно быть числом"
                                }}
                                render={({field: {onChange, onBlur, value, name, ref}}) => (
                                    <NumberInput
                                        value={value === '' ? undefined : Number(value)}
                                        onChange={(_valueAsString, valueAsNumber) => onChange(isNaN(valueAsNumber) ? '' : valueAsNumber)}
                                        onBlur={onBlur}
                                        allowMouseWheel
                                        step={1}
                                    >
                                        <NumberInputField name={name} ref={ref} placeholder="Начальная температура"/>
                                    </NumberInput>
                                )}
                            />
                        </HStack>
                        <FormErrorMessage ml="190px">{errors.temperature_start?.message}</FormErrorMessage>
                    </FormControl>

                    <FormControl isRequired isInvalid={!!errors.t_air}>
                        <HStack align="center">
                            <FormLabel htmlFor="t_air" mb="0" minW="180px">Температура воздуха
                                (°C):</FormLabel>
                            <Controller
                                name="t_air"
                                control={control}
                                rules={{
                                    required: "Это поле обязательно",
                                    validate: value => value !== '' && !isNaN(parseFloat(value as unknown as string)) || "Должно быть числом"
                                }}
                                render={({field: {onChange, onBlur, value, name, ref}}) => ( // Добавили ref
                                    <NumberInput
                                        value={value === '' ? undefined : Number(value)}
                                        onChange={(_valueAsString, valueAsNumber) => onChange(isNaN(valueAsNumber) ? '' : valueAsNumber)}
                                        onBlur={onBlur}
                                        allowMouseWheel
                                        step={1}
                                    >
                                        <NumberInputField name={name} ref={ref} placeholder="Температура воздуха"/>
                                    </NumberInput>
                                )}
                            />
                        </HStack>
                        <FormErrorMessage ml="190px">{errors.t_air?.message}</FormErrorMessage>
                    </FormControl>
                </VStack>
            </Box>

            <Button type="submit" colorScheme="teal" isLoading={isSubmitting} size="lg" mt={4}
                    width="full">
                Отправить
            </Button>
        </VStack>
    );
};

export default StockInputPage;