// analytics.js
(function() {
	// Fetch the runtime configuration
	fetch('config/config.json')
	.then(response => {
		if (!response.ok) {
			throw new Error('Configuration file not found');
		}
		return response.json();
	})
	.then(config => {
		if (!config.GA_KEY) {
			throw new Error('GA_KEY is missing in the configuration');
		}

		// Create the script tag for Google Tag Manager
		const scriptTag = document.createElement('script');
		scriptTag.async = true;
		scriptTag.src = `https://www.googletagmanager.com/gtag/js?id=${config.GA_KEY}`;
		document.head.appendChild(scriptTag);

		// Initialize Google Analytics
		window.dataLayer = window.dataLayer || [];

		function gtag() { dataLayer.push(arguments); }

		gtag('js', new Date());
		gtag('config', config.GA_KEY);
	})
	.catch(error => console.warn('GA setup skipped:', error.message));
})();