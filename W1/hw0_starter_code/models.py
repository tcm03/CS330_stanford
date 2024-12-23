"""
Classes defining user and item latent representations in
factorization models.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class ScaledEmbedding(nn.Embedding):
    """
    Embedding layer that initialises its values
    to using a normal variable scaled by the inverse
    of the embedding dimension.
    """

    def reset_parameters(self):
        """
        Initialize parameters.
        """

        self.weight.data.normal_(0, 1.0 / self.embedding_dim)
        if self.padding_idx is not None:
            self.weight.data[self.padding_idx].fill_(0)


class ZeroEmbedding(nn.Embedding):
    """
    Embedding layer that initialises its values
    to zero.

    Used for biases.
    """

    def reset_parameters(self):
        """
        Initialize parameters.
        """

        self.weight.data.zero_()
        if self.padding_idx is not None:
            self.weight.data[self.padding_idx].fill_(0)


class MultiTaskNet(nn.Module):
    """
    Multitask factorization representation.

    Encodes both users and items as an embedding layer; the likelihood score
    for a user-item pair is given by the dot product of the item
    and user latent vectors. The numerical score is predicted using a small MLP.

    Parameters
    ----------

    num_users: int
        Number of users in the model.
    num_items: int
        Number of items in the model.
    embedding_dim: int, optional
        Dimensionality of the latent representations.
    layer_sizes: list
        List of layer sizes to for the regression network.
    sparse: boolean, optional
        Use sparse gradients.
    embedding_sharing: boolean, optional
        Share embedding representations for both tasks.

    """

    def __init__(self, num_users, num_items, embedding_dim=32, layer_sizes=[96, 64],
                 sparse=False, embedding_sharing=True):

        super().__init__()

        self.embedding_dim = embedding_dim

        #********************************************************
        #******************* YOUR CODE HERE *********************
        #********************************************************

        self.U = ScaledEmbedding(
            num_embeddings = num_users,
            embedding_dim = embedding_dim,
            sparse = sparse
        )
        self.Q = ScaledEmbedding(
            num_embeddings = num_items,
            embedding_dim = embedding_dim,
            sparse = sparse
        )
        self.A = ZeroEmbedding(
            num_embeddings = num_users,
            embedding_dim = 1,
            sparse = sparse
        )
        self.B = ZeroEmbedding(
            num_embeddings = num_items,
            embedding_dim = 1,
            sparse = sparse
        )

        self.embedding_sharing = embedding_sharing
        if embedding_sharing == False:
            self.Up = ScaledEmbedding(
                num_embeddings = num_users,
                embedding_dim = embedding_dim,
                sparse = sparse
            )
            self.Qp = ScaledEmbedding(
                num_embeddings = num_items,
                embedding_dim = embedding_dim,
                sparse = sparse
            )

        self.mlp = nn.Sequential(
            nn.Linear(layer_sizes[0], layer_sizes[1]),
            nn.ReLU(),
            nn.Linear(layer_sizes[1], 1)
        )

        #********************************************************
        #********************************************************
        #********************************************************

    def forward(self, user_ids, item_ids):
        """
        Compute the forward pass of the representation.

        Parameters
        ----------

        user_ids: tensor
            A tensor of integer user IDs of shape (batch,)
        item_ids: tensor
            A tensor of integer item IDs of shape (batch,)

        Returns
        -------

        predictions: tensor
            Tensor of user-item interaction predictions of shape (batch,)
        score: tensor
            Tensor of user-item score predictions of shape (batch,)
        """
        #********************************************************
        #******************* YOUR CODE HERE *********************
        #********************************************************

        U_emb = self.U(user_ids)
        Q_emb = self.Q(item_ids)
        A_emb = self.A(user_ids)
        B_emb = self.B(item_ids)
        UQ_dot = torch.einsum('bd, bd -> b', U_emb, Q_emb).unsqueeze(-1)
        UQ = UQ_dot + A_emb + B_emb 
        predictions = UQ.squeeze(-1) # (batch,): user-item interaction log probability

        if self.embedding_sharing == True:
            mlp_input = torch.cat([U_emb, Q_emb, U_emb * Q_emb], dim = 1)
            score = self.mlp(mlp_input).squeeze(-1)
        else:
            Up_emb = self.Up(user_ids)
            Qp_emb = self.Qp(item_ids)
            mlp_input = torch.cat([Up_emb, Qp_emb, Up_emb * Qp_emb], dim = 1)
            score = self.mlp(mlp_input).squeeze(-1)

        #********************************************************
        #********************************************************
        #********************************************************
        ## Make sure you return predictions and scores of shape (batch,)
        if (len(predictions.shape) > 1) or (len(score.shape) > 1):
            raise ValueError("Check your shapes!")
        
        return predictions, score