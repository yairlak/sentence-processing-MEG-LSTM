def test_LSTM(sentences, vocab, settings):
    import torch
    import lstm
    from tqdm import tqdm
    import numpy as np

    model = torch.load(settings.LSTM_pretrained_model)
    model.rnn.flatten_parameters()
    # hack the forward function to send an extra argument containing the model parameters
    model.rnn.forward = lambda input, hidden: lstm.forward(model.rnn, input, hidden)

    # output buffers
    fixed_length_arrays = False
    if fixed_length_arrays:
        vectors = np.zeros((len(sentences), 2 *model.nhid*model.nlayers, max_length))
        log_probabilities =  np.zeros((len(sentences), max_length))
        gates = {k: np.zeros((len(sentences), model.nhid*model.nlayers, max_length)) for k in ['in', 'forget', 'out', 'c_tilde']}
    else:
        vectors = [np.zeros((2*model.nhid*model.nlayers, len(s))) for s in tqdm(sentences)] #np.zeros((len(sentences), 2 *model.nhid*model.nlayers, max_length))
        log_probabilities = [np.zeros(len(s)) for s in tqdm(sentences)] # np.zeros((len(sentences), max_length))
        gates = {k: [np.zeros((model.nhid*model.nlayers, len(s))) for s in tqdm(sentences)] for k in ['in', 'forget', 'out', 'c_tilde']} #np.zeros((len(sentences), model.nhid*model.nlayers, max_length)) for k in ['in', 'forget', 'out', 'c_tilde']}

    for i, s in enumerate(tqdm(sentences)):
        #sys.stdout.write("{}% complete ({} / {})\r".format(int(i/len(sentences) * 100), i, len(sentences)))
        out = None
        # reinit hidden
        hidden = model.init_hidden(1)
        # intitialize with end of sentence
        inp = torch.autograd.Variable(torch.LongTensor([[vocab.word2idx[args.eos_separator]]]))
        # if args.cuda:
        #     inp = inp.cuda()
        out, hidden = model(inp, hidden)
        out = torch.nn.functional.log_softmax(out[0]).unsqueeze(0)
        for j, w in enumerate(s):
            # store the surprisal for the current word
            log_probabilities[i][j] = out[0,0,vocab.word2idx[w]].data[0]

            inp = torch.autograd.Variable(torch.LongTensor([[vocab.word2idx[w]]]))
            # if args.cuda:
            #     inp = inp.cuda()
            out, hidden = model(inp, hidden)
            out = torch.nn.functional.log_softmax(out[0]).unsqueeze(0)

            vectors[i][:,j] = torch.cat([h.data.view(1,1,-1) for h in hidden],2).cpu().numpy()
            # we can retrieve the gates thanks to the hacked function
            for k, gates_k in gates.items():
                gates_k[i][:,j] = torch.cat([g[k].data for g in model.rnn.last_gates],1).cpu().numpy()

    return out