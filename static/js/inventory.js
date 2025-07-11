

// Parse the JSON data passed from the view
    const chartData = JSON.parse('{{ warehouse_json|escapejs }}');
// Initialize arrays for each dataset
    const totalPurchase = [];
    const totalManufacture = [];
    const totalExistingIn = [];
    const totalOperationsOut = [];
    const totalSold = [];
    const totalAvailable = [];
    const totalTransferIn = [];
    const totalTransferOut = [];
    const totalReplacementOut = [];
    const totalStock = [];

    // Populate arrays for each dataset
    chartData.labels.forEach((label, index) => {
        totalPurchase.push(chartData.total_purchase[index] || 0);
        totalManufacture.push(chartData.total_manufacture[index] || 0);
        totalExistingIn.push(chartData.total_existing_in[index] || 0);
        totalOperationsOut.push(chartData.total_operations_out[index] || 0);
        totalSold.push(chartData.total_sold[index] || 0);
        totalAvailable.push(chartData.total_available[index] || 0);
        totalTransferIn.push(chartData.total_transfer_in[index] || 0);
        totalTransferOut.push(chartData.total_transfer_out[index] || 0);
        totalReplacementOut.push(chartData.total_replacement_out[index] || 0);
        totalStock.push(chartData.total_stock[index] || 0);
    });

    // Calculate the max y-axis value
    const maxYValue = Math.max(
        ...totalPurchase,
        ...totalSold,
        ...totalAvailable,
        ...totalManufacture,
        ...totalTransferIn,
        ...totalTransferOut,
        ...totalReplacementOut,
        ...totalStock,
    ) * 1.4;


    // Bar chart
    const ctxBar = document.getElementById('barChart').getContext('2d');
    const barChart = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [

                {
                    label: 'Total Stock',
                    data: totalStock,
                     backgroundColor: 'rgba(76, 175, 80, 0.5)',  // Green
                    borderColor: 'rgba(76, 175, 80, 1)',        // Dark Green
                    borderWidth: 1
                },                


                {
                    label: 'Total Purchase',
                    data: totalPurchase,
                    backgroundColor: 'rgba(33, 150, 243, 0.5)', // Blue
                    borderColor: 'rgba(33, 150, 243, 1)',       // Dark Blue
                    borderWidth: 1
                },

                {
                    label: 'Total Existing',
                    data: totalExistingIn,
                    backgroundColor: 'rgba(255, 193, 7, 0.5)',  // Amber
                    borderColor: 'rgba(255, 193, 7, 1)',        // Dark Amber
                    borderWidth: 1
                },
                {
                    label: 'Total Manufacture',
                    data: totalManufacture,
                    backgroundColor: 'rgba(255, 193, 7, 0.5)',  // Amber
                    borderColor: 'rgba(255, 193, 7, 1)',        // Dark Amber
                    borderWidth: 1
                },
                {
                    label: 'Total Transfer In',
                    data: totalTransferIn,
                    backgroundColor: 'rgba(0, 188, 212, 0.5)', // Teal
                    borderColor: 'rgba(0, 188, 212, 1)',       // Dark Teal
                    borderWidth: 1
                },
               
                {
                    label: 'Total Sold',
                    data: totalSold,
                    backgroundColor: 'rgba(255, 87, 34, 0.5)',  // Deep Orange
                    borderColor: 'rgba(255, 87, 34, 1)',        // Dark Deep Orange
                    borderWidth: 1
                },
                {
                    label: 'Total Operations Out',
                    data: totalOperationsOut,
                    backgroundColor: 'rgba(0, 150, 136, 0.5)',  // Sea Green
                    borderColor: 'rgba(0, 150, 136, 1)',        // Dark Sea Green
                    borderWidth: 1
                },
                
               
                {
                    label: 'Total Transfer Out',
                    data: totalTransferOut,
                    backgroundColor: 'rgba(255, 152, 0, 0.5)',  // Orange
                    borderColor: 'rgba(255, 152, 0, 1)',        // Dark Orange
                    borderWidth: 1
                },
                {
                    label: 'Total Replacement Out',
                    data: totalReplacementOut,
                    backgroundColor: 'rgba(0, 150, 136, 0.5)',  // Sea Green
                    borderColor: 'rgba(0, 150, 136, 1)',        // Dark Sea Green
                    borderWidth: 1
                },
                {
                    label: 'Total Available',
                    data: totalAvailable,
                    backgroundColor: 'rgba(0, 150, 136, 1)',  // Pink
                    borderColor: 'rgba(0, 150, 136, 1)',        // Dark Pink
                    borderWidth: 1
                },
              
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: maxYValue
                }
            }
        }
    });



    // Show Django message modal if there are messages
    document.addEventListener("DOMContentLoaded", function() {
     const messageModal = document.getElementById('messageModal');
        if (messageModal) {
            const messagesContainer = document.getElementById('messagesContainer');
            if (messagesContainer && messagesContainer.children.length > 0) {
                const modalInstance = new bootstrap.Modal(messageModal);
                modalInstance.show();
            }
        }
    });
    


