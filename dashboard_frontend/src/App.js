import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css'; // Supondo que existe um App.css para estilos básicos

// URL da API de predição (substituir pelo URL real do API Gateway deployado)
const API_ENDPOINT = 'YOUR_API_GATEWAY_ENDPOINT_HERE/predict'; 

function App() {
  const [turbineData, setTurbineData] = useState([]); // Para dados históricos de sensores
  const [liveDataPoint, setLiveDataPoint] = useState(null); // Para um ponto de dado "ao vivo" para predição
  const [prediction, setPrediction] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Simulação de recebimento de dados de sensores (em um app real, viria de um WebSocket ou polling)
  // Para este exemplo, vamos usar um formulário simples para inserir dados para predição
  const [manualInput, setManualInput] = useState({
    gearbox_temperature_c_mean: 75.0,
    gearbox_temperature_c_std: 2.5,
    gearbox_temperature_c_min: 72.0,
    gearbox_temperature_c_max: 78.0,
    gearbox_temperature_c_median: 75.0,
    generator_power_kw_mean: 1600.0,
    generator_power_kw_std: 250.0,
    generator_power_kw_min: 1200.0,
    generator_power_kw_max: 2000.0,
    generator_power_kw_median: 1600.0,
    rotation_speed_rpm_mean: 15.0,
    rotation_speed_rpm_std: 3.0,
    rotation_speed_rpm_min: 10.0,
    rotation_speed_rpm_max: 20.0,
    rotation_speed_rpm_median: 15.0,
    vibration_x_g_mean: 0.15,
    vibration_x_g_std: 0.03,
    vibration_x_g_min: 0.1,
    vibration_x_g_max: 0.2,
    vibration_x_g_median: 0.15,
    vibration_y_g_mean: 0.16,
    vibration_y_g_std: 0.04,
    vibration_y_g_min: 0.11,
    vibration_y_g_max: 0.22,
    vibration_y_g_median: 0.16,
    wind_speed_m_s_mean: 8.0,
    wind_speed_m_s_std: 2.0,
    wind_speed_m_s_min: 5.0,
    wind_speed_m_s_max: 12.0,
    wind_speed_m_s_median: 8.0
    // Adicionar todas as features esperadas pelo modelo, conforme model_columns.json
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setManualInput(prev => ({ ...prev, [name]: parseFloat(value) || 0 }));
  };

  const fetchPrediction = useCallback(async (dataToPredict) => {
    if (!API_ENDPOINT || API_ENDPOINT === 'YOUR_API_GATEWAY_ENDPOINT_HERE/predict') {
      setError('API Endpoint não configurado. Verifique a constante API_ENDPOINT.');
      setPrediction({ predicted_status: 'Erro de Configuração', predicted_label: -1 });
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToPredict),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || `Erro HTTP: ${response.status}`);
      }
      const result = await response.json();
      setPrediction(result);
    } catch (err) {
      console.error('Erro ao buscar predição:', err);
      setError(err.message);
      setPrediction(null);
    }
    setIsLoading(false);
  }, []);

  const handlePredictClick = () => {
    fetchPrediction(manualInput);
  };

  // Simulação de dados históricos para gráfico (substituir por dados reais ou de outra API)
  useEffect(() => {
    const generateSampleData = () => {
      const data = [];
      for (let i = 0; i < 30; i++) {
        data.push({
          name: `T-${i}`,
          temperature: 60 + Math.random() * 20,
          vibration: 0.1 + Math.random() * 0.1,
          power: 1400 + Math.random() * 200,
        });
      }
      return data;
    };
    setTurbineData(generateSampleData());
  }, []);

  return (
    <div className="App p-4">
      <header className="App-header mb-8">
        <h1 className="text-3xl font-bold text-center text-blue-600">Dashboard de Manutenção Preditiva - Turbinas Eólicas</h1>
      </header>

      <section className="prediction-input bg-gray-100 p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-2xl font-semibold mb-4 text-gray-700">Realizar Predição Manual</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          {Object.keys(manualInput).map(key => (
            <div key={key} className="form-group">
              <label htmlFor={key} className="block text-sm font-medium text-gray-600 capitalize">{key.replace(/_/g, ' ')}:</label>
              <input 
                type="number" 
                name={key} 
                id={key} 
                value={manualInput[key]} 
                onChange={handleInputChange} 
                step="0.01"
                className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
          ))}
        </div>
        <button 
          onClick={handlePredictClick} 
          disabled={isLoading}
          className="px-6 py-2 bg-blue-500 text-white font-semibold rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50"
        >
          {isLoading ? 'Processando...' : 'Obter Predição'}
        </button>
        {error && <p className="text-red-500 mt-4">Erro: {error}</p>}
        {prediction && (
          <div className={`mt-6 p-4 rounded-md ${prediction.predicted_label === 0 ? 'bg-green-100 text-green-700' : prediction.predicted_label === -1 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
            <h3 className="text-lg font-semibold">Resultado da Predição:</h3>
            <p>Status: <span className="font-bold">{prediction.predicted_status}</span> (Label: {prediction.predicted_label})</p>
            {prediction.prediction_probabilities && prediction.prediction_probabilities !== "N/A" && (
              <p>Probabilidades: Normal: {(prediction.prediction_probabilities[0] * 100).toFixed(2)}%, Falha Caixa Eng: {(prediction.prediction_probabilities[1] * 100).toFixed(2)}%, Falha Vibração: {(prediction.prediction_probabilities.length > 2 ? (prediction.prediction_probabilities[2] * 100).toFixed(2) : 'N/A')}%</p>
            )}
          </div>
        )}
      </section>

      <section className="historical-data bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-semibold mb-4 text-gray-700">Dados Históricos (Exemplo)</h2>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={turbineData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis yAxisId="left" label={{ value: 'Temperatura (°C)', angle: -90, position: 'insideLeft' }} />
            <YAxis yAxisId="right" orientation="right" label={{ value: 'Vibração (g)', angle: -90, position: 'insideRight' }}/>
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="temperature" stroke="#8884d8" activeDot={{ r: 8 }} name="Temperatura"/>
            <Line yAxisId="right" type="monotone" dataKey="vibration" stroke="#82ca9d" name="Vibração"/>
          </LineChart>
        </ResponsiveContainer>
      </section>
    </div>
  );
}

export default App;

