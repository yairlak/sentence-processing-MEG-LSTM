import os.path as op
import os
import numpy as np
from sklearn.model_selection import train_test_split
from functions import load_settings_params as lsp
from functions import model_fitting_and_evaluation as mfe
from functions import extract_activations_from_LSTM
# from functions import plot_results as pr
import torch
import sys
import pickle
sys.path.append(os.path.abspath('../src/word_language_model'))
import data

# --------- Main script -----------
print('Load settings and parameters')
settings = lsp.settings()
params = lsp.params()
preferences = lsp.preferences()

# Load Stimuli
print('Loading number of open nodes data')
with open(op.join(settings.path2LSTMdata, settings.bnc_data), 'rb') as f:
    stimuli = pickle.load(f)
    sentences = [i[0] for i in stimuli]
    meta = [i[2] for i in stimuli]
    # For debug
    sentences = [s for i, s in enumerate(sentences) if i in range(100)]
    meta = [s for i, s in enumerate(meta) if i in range(100)]
    # ------
    num_open_nodes = [i['all'] for i in meta]
    y = np.asarray([item for sublist in num_open_nodes for item in sublist])

# Load vocabulary
vocab = data.Dictionary(settings.vocabulary_file)

# Load LSTM model
print('Loading models...')
if preferences.load_pretested_LSTM:
    #Load LSTM data
    print('Loading pre-tested LSTM model on test sentences...')
    LSTM_data = np.load(op.join(settings.path2LSTMdata, settings.LSTM_pretested_file_name))
    print(LSTM_data.files)
    LSTM_data = LSTM_data['vectors']
    print(LSTM_data.shape)
else:
    LSTM_data = extract_activations_from_LSTM.test_LSTM(sentences, vocab, settings.eos_separator, settings)
    X = LSTM_data['vectors']
    X = [x.transpose() for x in X] # Transpose elements
    X = np.vstack(X) # Stack into a matrix (num-words X num-units)


pkl_filename = 'Regression_number_of_open_nodes_MODEL_' + settings.LSTM_pretrained_model + '.pckl'
if not op.exists(op.join(settings.path2output, pkl_filename)):

    # ## Split data to train/test sets
    print('Splitting data to train/test sets')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=1./params.CV_fold,
                                                    random_state=params.seed_split)

    models = {}
    # ############ Ridge Regression ############
    if preferences.run_Ridge:
        print('Fitting a ridge model for  time point ')
        settings.method = 'Ridge'
        # Train model
        model_ridge = mfe.train_model(X_train, y_train, settings, params)
        # Evaluate model on test set
        ridge_scores_test = mfe.evaluate_model(model_ridge, X_test, y_test, settings, params)
        # Generate and save figures
        # plt = pr.regularization_path(model_ridge, settings, params)
        file_name = 'Ridge_coef_and_R_squared_vs_regularization_size_channel_' + \
                     '.png'
        # plt.savefig(op.join(settings.path2figures, file_name))
        # plt.close()
        models['model_ridge'] = model_ridge
        models['ridge_scores_test'] = ridge_scores_test
    # ##########################################

    # ############ Lasso Regression ############
    if preferences.run_LASSO:
        print('Fitting a lasso model for')
        settings.method = 'Lasso'
        # Train model
        model_lasso = mfe.train_model(X_train, y_train, settings, params)
        # Evaluate model on test set
        lasso_scores_test = mfe.evaluate_model(model_lasso, X_test, y_test, settings, params)
        # Generate and save figures
        # plt = pr.regularization_path(model_lasso, settings, params)
        file_name = 'Lasso_coef_and_R_squared_vs_regularization_size_channel_' + \
                    '_timepoint_' + str(time_point) + '.png'
        # plt.savefig(op.join(settings.path2figures, file_name))
        # plt.close()
        models['model_lasso'] = model_lasso
        models['lasso_scores_test'] = lasso_scores_test
        print('Done fitting')
    # ##########################################

    # ############ Elastic-net Regression #####
    if preferences.run_ElasticNet:
        print('Fitting an elastic-net model for channel ')
        settings.method = 'Elastic_net'
        model_enet = mfe.train_model(X_train, y_train, settings, params)
        # Evaluate model on test set
        enet_scores_test = mfe.evaluate_model(model_enet, X_test, y_test, settings, params)
        # Generate and save figures
        # plt = pr.regularization_path(model_enet, settings, params)
        file_name = 'Elastic_net_coef_and_R_squared_vs_regularization_size_channel_' + '.png'
        # plt.savefig(op.join(settings.path2figures, file_name))
        # plt.close()
        models['model_enet'] = model_enet
        models['enet_scores_test'] = model_enet
    # ##########################################

    # ############# Save models and results #####
    with open(op.join(settings.path2output, pkl_filename), "wb") as f:
        pickle.dump(models, f)
        pickle.dump(settings, f)
        pickle.dump(params, f)
    print('Models for channel ' + ' time point ' + str(time_point) + 'were saved to Output folder')
