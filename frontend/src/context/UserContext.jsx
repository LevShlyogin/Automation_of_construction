import React, { createContext, useState } from "react";

export const UserContext = createContext();
    const [token, setToken] = useState(localStorage.getItem("awesomeLeadsToken"));

    useEffect(() => {
        const fetchUser = async () => {
            const requestOptions = {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: "Bearer " + token,
                },
            }
        };
    });
};