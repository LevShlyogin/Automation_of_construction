import React from 'react';
import './HelpPage.css'; // Подключаем стили

const HelpPage: React.FC = () => {
  return (
	<div className="help-page">
        <h1>Помощь</h1>
        <p>Здесь вы найдете ответы на часто задаваемые вопросы и инструкцию по использованию.</p>
        <form action="/" method="get">
            <button className="back-button" type="submit">На главную</button>
        </form>
	</div>
  );
};

export default HelpPage;
