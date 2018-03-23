import numpy
from scipy.stats import lognorm, norm


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

