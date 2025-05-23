import {createRootRoute} from "@tanstack/react-router"
import React, {Suspense} from "react"
import MainLayout from "../components/Common/MainLayout"
import NotFound from "../components/Common/NotFound"

const loadDevtools = () =>
    Promise.all([
        import("@tanstack/router-devtools"),
        import("@tanstack/react-query-devtools"),
    ]).then(([routerDevtools, reactQueryDevtools]) => {
        return {
            default: () => (
                <>
                    <routerDevtools.TanStackRouterDevtools/>
                    <reactQueryDevtools.ReactQueryDevtools/>
                </>
            ),
        }
    })

const TanStackDevtools =
    process.env.NODE_ENV === "production" ? () => null : React.lazy(loadDevtools)

export const Route = createRootRoute({
    component: () => (
        <>
            <MainLayout/>
            <Suspense>
                <TanStackDevtools/>
            </Suspense>
        </>
    ),
    notFoundComponent: () => <NotFound/>,
})
