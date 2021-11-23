import React, { useEffect, useState } from 'react'
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null)

	const getStats = () => {

        // fetch(`http://localhost:8100/route/stats`)
        fetch(`http://kafka-ti-acit3855.eastus2.cloudapp.azure.com/processing/route/stats`)
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Stats")
                setStats(result);
                setIsLoaded(true);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
    useEffect(() => {
		const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
		return() => clearInterval(interval);
    }, [getStats]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return(
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
					<tbody>
						<tr>
							<th>Train Routes</th>
							<th>Ticket Bookings</th>
						</tr>
						<tr>
							<td># Routes: {stats['count_routes']}</td>
							<td># Bookings: {stats['count_tickets']}</td>
						</tr>
						<tr>
							<td colspan="2">Max Route Length (Hours): {stats['max_route_length']}</td>
						</tr>
						<tr>
							<td colspan="2">Max Tickets Bought: {stats['max_tickets_bought']}</td>
						</tr>
					</tbody>
                </table>
                <h3>Last Updated: {stats['date_created']}</h3>
            </div>
        )
    }
}
