import ReactDOM from 'react-dom/client'
import {
	createBrowserRouter,
	RouterProvider,
} from "react-router-dom";
import "leaflet/dist/leaflet.css"
import "./css/pour-leaflet.css"
import AutourDeMoi from './pages/autourDeMoi.tsx';
import 'bootstrap/dist/css/bootstrap.min.css';


const router = createBrowserRouter([
    {
        path: "/autourDeMoi",
        element: <AutourDeMoi />,
    },
    {
        path: "",
        element: <AutourDeMoi />,
    },

]);

ReactDOM.createRoot(document.getElementById('root')!).render(
    //<React.StrictMode>
    <RouterProvider router={router} />
    // </React.StrictMode>,
)
