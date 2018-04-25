import numpy
from scipy.stats import lognorm, norm
import folium
from owslib.wms import WebMapService


class PlotUtil:
    @staticmethod
    def sample_lognormal_cdf_alt(mean: float, std: float, sample_size: int):
        dist = lognorm(s = std, loc = 0, scale = numpy.exp(mean))
        start = dist.ppf(0.001)  # cdf inverse
        end = dist.ppf(0.999)  # cdf inverse
        x = numpy.linspace(start, end, sample_size)
        y = dist.cdf(x)
        return x, y

    @staticmethod
    def sample_lognormal_cdf(location: float, scale: float, sample_size: int):
        # convert location and scale parameters to the normal mean and std
        mean = numpy.log(numpy.square(location) / numpy.sqrt(scale + numpy.square(location)))
        std = numpy.sqrt(numpy.log((scale / numpy.square(location)) + 1))
        dist = lognorm(s = std, loc = 0, scale = numpy.exp(mean))
        start = dist.ppf(0.001)  # cdf inverse
        end = dist.ppf(0.999)  # cdf inverse
        x = numpy.linspace(start, end, sample_size)
        y = dist.cdf(x)
        return x, y

    @staticmethod
    def sample_normal_cdf(mean: float, std: float, sample_size: int):
        dist = norm(mean, std)
        start = dist.ppf(0.001)  # cdf inverse
        end = dist.ppf(0.999)  # cdf inverse
        x = numpy.linspace(start, end, sample_size)
        y = dist.cdf(x)
        return x, y

    @staticmethod
    def get_x_y(disttype: str, alpha: float, beta: float):
        if disttype == 'LogNormal':
            return PlotUtil.sample_lognormal_cdf_alt(alpha, beta, 200)
        if disttype == 'Normal':
            return PlotUtil.sample_lognormal_cdf(alpha, beta, 200)
        if disttype == 'standardNormal':
            return PlotUtil.sample_normal_cdf(alpha, beta, 200)
        
    @staticmethod
    def get_wms_map(layers_config: list):
        """
        return map with wms layers
        
        layers_config: list of layer config
        [{
            'id': '12345fe',
            'name': 'hello',
            'style': 'hello-style'
        },{}]
        """
        m = folium.Map(width=600, height=400)
        url = 'http://incore2-geoserver.ncsa.illinois.edu:9999/geoserver/incore/wms' 
        bbox_all = [9999, 9999, -9999, -9999]
        for layer in layers_config:
            wms_layer = folium.features.WmsTileLayer(url, name=layer['name'], fmt='image/png',transparent=True,
                                                    layers='incore:'+layer['id'], styles=layer['style'])
            wms_layer.add_to(m)
            wms = WebMapService(url) 
            bbox = wms[layer['id']].boundingBox 
            # merge bbox 
            if bbox[0] < bbox_all[0]: bbox_all[0] = bbox[0]
            if bbox[1] < bbox_all[1]: bbox_all[1] = bbox[1]
            if bbox[2] > bbox_all[2]: bbox_all[2] = bbox[2]
            if bbox[3] > bbox_all[3]: bbox_all[3] = bbox[3]

        folium.LayerControl().add_to(m)
        bounds = ((bbox_all[1], bbox_all[0]), (bbox_all[3],bbox_all[2]))
        m.fit_bounds(bounds)
        return m
    
    @staticmethod
    def get_geopandas_map(geodataframe):
        """
        return map with geo dataframe
        """
        m = folium.Map(width=600, height=400)
        folium.GeoJson(geodataframe.to_json(), name='hospital').add_to(m)
        ext = geodataframe.total_bounds
        m.fit_bounds([[ext[1], ext[0]], [ext[3], ext[2]]])
        return m
        

