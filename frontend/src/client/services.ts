import type { CancelablePromise } from './core/CancelablePromise';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

import type { TurbineInfo,TurbineValves,ValveCreate,ValveInfo_Input,ValveInfo_Output,CalculationParams,CalculationResultDB } from './models';

export type TDataTurbinesGetValvesByTurbineEndpoint = {
                turbineName: string
                
            }
export type TDataTurbinesCreateTurbine = {
                requestBody: TurbineInfo
                
            }
export type TDataTurbinesDeleteTurbine = {
                turbineId: number
                
            }

export class TurbinesService {

	/**
	 * Получить все турбины
	 * Получить список всех турбин.
	 * @returns TurbineInfo Successful Response
	 * @throws ApiError
	 */
	public static turbinesGetAllTurbines(): CancelablePromise<Array<TurbineInfo>> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/turbines/',
		});
	}

	/**
	 * Получить клапаны по имени турбины
	 * Получить список клапанов для заданной турбины.
	 * @returns TurbineValves Successful Response
	 * @throws ApiError
	 */
	public static turbinesGetValvesByTurbineEndpoint(data: TDataTurbinesGetValvesByTurbineEndpoint): CancelablePromise<TurbineValves> {
		const {
turbineName,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/turbines/{turbine_name}/valves/',
			path: {
				turbine_name: turbineName
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Создать турбину
	 * Создать новую турбину.
	 * @returns TurbineInfo Successful Response
	 * @throws ApiError
	 */
	public static turbinesCreateTurbine(data: TDataTurbinesCreateTurbine): CancelablePromise<TurbineInfo> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/turbines',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Удалить турбину
	 * Удалить турбину по ID.
	 * @returns void Successful Response
	 * @throws ApiError
	 */
	public static turbinesDeleteTurbine(data: TDataTurbinesDeleteTurbine): CancelablePromise<void> {
		const {
turbineId,
} = data;
		return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/turbines/{turbine_id}',
			path: {
				turbine_id: turbineId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export type TDataValvesCreateValve = {
                requestBody: ValveCreate
                
            }
export type TDataValvesUpdateValve = {
                requestBody: ValveInfo_Input
valveId: number
                
            }
export type TDataValvesDeleteValve = {
                valveId: number
                
            }
export type TDataValvesGetTurbineByValveName = {
                valveName: string
                
            }

export class ValvesService {

	/**
	 * Получить все клапаны
	 * Получить список всех клапанов.
	 * @returns ValveInfo_Output Successful Response
	 * @throws ApiError
	 */
	public static valvesGetValves(): CancelablePromise<Array<ValveInfo_Output>> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/valves',
		});
	}

	/**
	 * Создать клапан
	 * Создать новый клапан.
	 * @returns ValveInfo_Output Successful Response
	 * @throws ApiError
	 */
	public static valvesCreateValve(data: TDataValvesCreateValve): CancelablePromise<ValveInfo_Output> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/valves/',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Обновить клапан
	 * Обновить данные о клапане.
	 * @returns ValveInfo_Output Successful Response
	 * @throws ApiError
	 */
	public static valvesUpdateValve(data: TDataValvesUpdateValve): CancelablePromise<ValveInfo_Output> {
		const {
requestBody,
valveId,
} = data;
		return __request(OpenAPI, {
			method: 'PUT',
			url: '/api/v1/valves/{valve_id}',
			path: {
				valve_id: valveId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Удалить клапан
	 * Удалить клапан по ID.
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static valvesDeleteValve(data: TDataValvesDeleteValve): CancelablePromise<Record<string, unknown>> {
		const {
valveId,
} = data;
		return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/valves/{valve_id}',
			path: {
				valve_id: valveId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Получить турбину по имени клапана
	 * Получить турбину по имени клапана.
	 * @returns TurbineInfo Successful Response
	 * @throws ApiError
	 */
	public static valvesGetTurbineByValveName(data: TDataValvesGetTurbineByValveName): CancelablePromise<TurbineInfo> {
		const {
valveName,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/valves/{valve_name}/turbine',
			path: {
				valve_name: valveName
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export type TDataCalculationsCalculate = {
                requestBody: CalculationParams
                
            }

export class CalculationsService {

	/**
	 * Выполнить расчет
	 * Выполнить расчет на основе параметров.
	 * @returns CalculationResultDB Successful Response
	 * @throws ApiError
	 */
	public static calculationsCalculate(data: TDataCalculationsCalculate): CancelablePromise<CalculationResultDB> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/calculate',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export type TDataResultsGetCalculationResults = {
                valveName: string
                
            }
export type TDataResultsDeleteCalculationResult = {
                resultId: number
                
            }

export class ResultsService {

	/**
	 * Получить результаты расчётов
	 * Получить список результатов расчётов для заданного клапана.
	 * @returns CalculationResultDB Successful Response
	 * @throws ApiError
	 */
	public static resultsGetCalculationResults(data: TDataResultsGetCalculationResults): CancelablePromise<Array<CalculationResultDB>> {
		const {
valveName,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/valves/{valve_name}/results/',
			path: {
				valve_name: valveName
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Удалить результат расчёта
	 * Удалить результат расчёта по ID.
	 * @returns void Successful Response
	 * @throws ApiError
	 */
	public static resultsDeleteCalculationResult(data: TDataResultsDeleteCalculationResult): CancelablePromise<void> {
		const {
resultId,
} = data;
		return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/results/{result_id}',
			path: {
				result_id: resultId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}