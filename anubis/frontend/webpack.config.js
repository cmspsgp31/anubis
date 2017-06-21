// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// webpack.config.js - Webpack config for the interface module

// This file is part of Anubis.

// Anubis is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Anubis is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.

const webpack = require('webpack');
const path = require('path');
const Compressor = require('compression-webpack-plugin');

const nodeEnv = process.env.NODE_ENV || 'development';
const isProd = nodeEnv == 'production';

module.exports = {
    devtool: '#inline-source-map',
    context: path.join(__dirname, './src'),
    entry: { js: './main.js' },
    output: {
        path: path.join(__dirname, '../app/static/anubis'),
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
        extensions: ['.js', '.jsx'],
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
    delete module.exports.devtool;

    module.exports.plugins.push(
        new webpack.optimize.UglifyJsPlugin({
            compress: {
                warnings: false,
            },
            output: {
                comments: false,
            },
            sourceMap: false,
        }),
        new webpack.optimize.AggressiveMergingPlugin(),
        new Compressor({
            asset: "[path].gz[query]",
            algorithm: "gzip",
            test: /\.js$|\.css$/,
            threshold: 10240,
            minRatio: 0.8,
        }),
    );
}
