const webpack = require('webpack');
const path = require('path');

const nodeEnv = process.env.NODE_ENV || 'development';
const isProd = nodeEnv == 'production';

module.exports = {
    devtool: isProd ? 'hidden-source-map' : 'cheap-eval-source-map',
    context: path.join(__dirname, './src'),
    entry: { js: './main.js' },
    output: {
        path: path.join(__dirname, './build'),
        filename: 'anubis.js',
    },
    module: {
        loaders: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loaders: ['babel-loader'],
            },
            {
                test: /\.json$/,
                loader: 'json',
            },
        ],
    },
    resolve: {
        extensions: ['', '.js', '.jsx'],
        modules: [
            path.resolve('./src'),
            'node_modules',
        ],
    },
    plugins: [
        new webpack.DefinePlugin({
            'process.env': {
                'NODE_ENV': JSON.stringify(nodeEnv),
            },
        }),
    ],
};

if (isProd) {
    module.exports.plugins.push(
        new webpack.optimize.UglifyJsPlugin({
            compress: {
                warnings: false,
            },
            output: {
                comments: false,
            },
            sourceMap: false,
        })
    );
}
