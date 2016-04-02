// Copyright © 2016, Ugo Pozo
//             2016, Câmara Municipal de São Paulo

// application_reducers.js - reducers that deal with the application state.

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


export const App = {
    ReducerMap: {
        'SET_GLOBAL_ERROR': (state, action) => {
            return state
                .set('globalError', action.payload)
                .set('showErrorDetails', false);
        },
        'SHOW_GLOBAL_ERROR_DETAILS': state => {
            return state.set('showErrorDetails', true);
        },
        'CLEAR_GLOBAL_ERROR': state => {
            return state.remove('globalError').remove('showErrorDetails');
        },
        'START_ACTION': (state, action) => {
            return state.set('currentAction', action.payload);
        },
        'CANCEL_ACTION': state => {
            return state.set('currentAction', null);
        },
    },
    keyPath: ['applicationData'],
};
