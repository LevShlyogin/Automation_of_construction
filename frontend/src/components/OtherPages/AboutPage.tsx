import React from 'react';
import './AboutPage.css'; // Подключаем стили

const AboutPage: React.FC = () => {
  return (
	<div className="about-page">
  	<h1>О программе</h1>
  	<p>Эта программа предназначена для расчета параметров турбин и их штоков.</p>
  	<form action="/" method="get">
        <button className="back-button" type="submit">На главную</button>
    </form>
	</div>
  );
};

export default AboutPage;
