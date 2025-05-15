import type {ApiError} from "./client"

export const emailPattern = {
    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
    message: "Invalid email address",
}

export const namePattern = {
    value: /^[A-Za-z\s\u00C0-\u017F]{1,30}$/,
    message: "Invalid name",
}

export const handleError = (err: ApiError, showToast: any) => {
    const errDetail = (err.body as any)?.detail
    let errorMessage = errDetail || "Something went wrong."
    if (Array.isArray(errDetail) && errDetail.length > 0) {
        errorMessage = errDetail[0].msg
    }
    showToast("Error", errorMessage, "error")
}
