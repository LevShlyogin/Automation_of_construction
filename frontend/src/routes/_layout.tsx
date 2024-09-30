// import { Flex, Spinner } from "@chakra-ui/react"
// import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"
// import { Route } from 'react-router-dom';
//
// import Sidebar from "../components/Common/Sidebar"
// import UserMenu from "../components/Common/UserMenu"
// import useAuth, { isLoggedIn } from "../hooks/useAuth"
//
// import CalculatorPage from './calculator'; // Это ваш компонент с логикой
//
//
// <RouterRoute path="/calculator" element={<ItemsPage />} />
//
// export const RouterRoute = createFileRoute("/_layout")({
//   component: Layout,
//   beforeLoad: async () => {
//     if (!isLoggedIn()) {
//       throw redirect({
//         to: "/login",
//       })
//     }
//   },
// })
//
// function Layout() {
//   const { isLoading } = useAuth()
//
//   return (
//     <Flex maxW="large" h="auto" position="relative">
//       <Sidebar />
//       {isLoading ? (
//         <Flex justify="center" align="center" height="100vh" width="full">
//           <Spinner size="xl" color="ui.main" />
//         </Flex>
//       ) : (
//         <Outlet />
//       )}
//       <UserMenu />
//     </Flex>
//   )
// }


import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
// import Layout from '../components/Common/Layout';
import CalculatorPage from './calculator'; // Ваш компонент для рендеринга страницы калькулятора

const LayoutRoutes = () => {
  return (
	<Router>
  	<Routes>
      	<Route path="/calculator" element={<CalculatorPage />} />
  	</Routes>
	</Router>
  );
};

export default LayoutRoutes;
