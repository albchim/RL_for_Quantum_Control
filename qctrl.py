'''
    Created on Oct 16, 2020

    @author: Alberto Chimenti

    Purpose: (PYTHON3 IMPLEMENTATION)
        General purpose Q-learning approach for optimal quantum control protocols
'''

#%%
import numpy as np
import scipy.special as sp

class Environment:

    def __init__(self, start=[0,0], mag_field=[-4, 0, +4], history=False):
        # Check coefficients
        if len(qtarget)!=len(qstart): 
            print("Warning ---> target and init coeffitients number don't match! \nExiting...") 
            exit
        ### Quantum state data (not sure whether to save it in the environement)
        #self.qtarget = qtarget
        #self.qstart = qstart
        self.history = history
        self.state = np.asarray(start)
        self.action_map = {i : mag_field[i] for i in range(len(mag_field))}
        if self.history == True:
            self.path = np.array(self.state)

    # the agent makes an action (0 is -bound, LAST is +bound)
    def move(self, action, qstate, dt, time_ev_func):
        '''
            Takes as input:
            - action index (INTEGER);
            - quantum state (COMPLEX VECTOR);
            - FUNCTION to use for time evolution;
            #- FUNCTION to use for computing the reward
        '''
        field = self.action_map[action]
        qstate = time_ev_func(qstate, dt, field)#, trotter=True)
        self.state = [self.state[0]+1, action]
        if self.history:
            self.path = np.append(self.path, [self.state], axis=0)
        return self.state, qstate

class Agent:

    n_states = 1
    n_actions = 1
    discount = 0.9
    max_reward = 1
    qtable = np.matrix([1])
    softmax = False
    sarsa = False
    
    # initialize
    def __init__(self, nstates, nactions, discount=0.9, max_reward=1, softmax=False, sarsa=False, qtable=None):
        self.nstates = nstates
        self.nactions = nactions
        self.discount = discount
        self.max_reward = max_reward
        self.softmax = softmax
        self.sarsa = sarsa
        # initialize Q table
        # The indexing will be index(t)*len(h)+index(h)
        self.qtable = np.ones([nstates*nactions, nactions], dtype = float) * max_reward / (1 - discount)
        if qtable is not None:
            qtable = np.array(qtable)
            if np.shape(qtable)==[nstates*nactions, nactions]:
                self.qtable = qtable
            else: 
                print("WARNING ----> Qtable size doesn't match given arguments \n [nstates*nactions, nactions]=", [nstates*nactions, nactions], "\n Given:", np.shape(qtable))

    def extract_state(self):
        state_dict = {
            'nstates' : self.nstates,
            'nactions' : self.nactions,
            'discount' : self.discount,
            'max_reward' : self.max_reward,
            'softmax' : self.softmax,
            'sarsa' : self.sarsa,
            'qtable' : self.qtable
            }
        return state_dict

    # action policy: implements epsilon greedy and softmax
    def select_action(self, state, epsilon):
        qval = self.qtable[state]
        prob = []
        if (self.softmax):
            # use Softmax distribution
            if epsilon == 0: epsilon = 1
            prob = sp.softmax(qval / epsilon)
        else:
            # assign equal value to all actions
            prob = np.ones(self.nactions) * epsilon / (self.nactions - 1)
            # the best action is taken with probability 1 - epsilon
            prob[np.argmax(qval)] = 1 - epsilon
        return np.random.choice(range(0, self.nactions), p = prob)
        
    # update function (Sarsa and Q-learning)
    def update(self, state, action, reward, next_state, alpha, epsilon):
        # find the next action (greedy for Q-learning, using the decision policy for Sarsa)
        next_action = self.select_action(next_state, 0)
        if (self.sarsa):
            next_action = self.select_action(next_state, epsilon)
        # calculate long-term reward with bootstrap method
        observed = reward + self.discount * self.qtable[next_state, next_action]
        # bootstrap update
        self.qtable[state, action] = self.qtable[state, action] * (1 - alpha) + observed * alpha

    # simple output directory selector
    def get_out_dir(self):
        if self.sarsa==True:
            name = 'sarsa'
        else:
            name = 'no_sarsa'
        if self.softmax==True:
            name = name + '_softmax'
        return name


def train_agent(agent, qtarget, qstart, start, mag_field, dt, time_ev_func, fidelity_func, episodes, episode_length, epsilon, alpha, verbose=None, check_norm=True):
    from tqdm import tqdm

    rewards = []
    for index in tqdm(range(0, episodes)):
        # initialize environment
        env = Environment(start=start, mag_field=mag_field)
        state = env.state
        qstate = qstart
        reward = 0
        # run episode
        for _ in range(0, episode_length):
            # find state index
            state_index = state[0] * len(mag_field) + state[1]
            # choose an action
            action = learner.select_action(state_index, epsilon[index])
            # the agent moves in the environment
            state, qstate = env.move(action, qstate, dt, time_ev_func)#, fidelity)
            # check norm conservation
            if check_norm and (np.abs(1 - fidelity_func(qstate, qstate)) > 1e-13):
                print("Warning ---> Norm is not conserved")
            # compute reward
            #if step == episode_length-1: # Uncomment if only the last reward has to be counted
            reward = fidelity_func(qtarget, qstate)
            # Q-learning update
            next_index = state[0] * len(mag_field) + state[1]
            learner.update(state_index, action, reward, next_index, alpha[index], epsilon[index])
        rewards.append(reward)
        # periodically save the agent
        if (verbose is not None) and ((index + 1) % verbose == 0):
            #agent_state = learner.extract_state()
            #name = 'agent'+'_'+str(a)+'.obj'
            #with open(out_dir / name, 'wb') as agent_file:
            #    dill.dump(agent_state, agent_file)
            print('\nEpisode ', index + 1, ': the agent has obtained fidelity eqal to', reward, '\nStarting from position ', qstart)
    return env, rewards


def get_time_grid(t_max, dt):
    span = np.arange(0, t_max, dt, dtype=float)
    tdict = {i : span[i] for i in range(len(span))}
    return tdict


############################################################################


if __name__ == "__main__":

    ########## Standard initialization
    from quantum_state import i, time_evolution, fidelity
    #import dill
    from pathlib import Path
    import matplotlib.pyplot as plt

    out_dir = Path("test")
    out_dir.mkdir(parents=True, exist_ok=True)

    episodes = 10000         # number of training episodes
    discount = 0.9          # exponential discount factor
    t_max = 3               # simulation time in seconds
    dt = 0.025               # timestep in seconds
    time_map = get_time_grid(t_max, dt)
    episode_length = len(time_map)         # maximum episode length
    mag_field = [-4, +4]
    nstates = episode_length*len(mag_field) # total number of states
    nactions = len(mag_field)              # total number of possible actions

    # Define target and starting state
    qtarget = np.array([0. + 0.j,-1/np.sqrt(2)-1/np.sqrt(2)*i])
    qstart = np.array([+1/np.sqrt(2)+1/np.sqrt(2)*i,0. + 0.j])

    a = 0.8
    # alpha value and epsilon
    alpha = np.ones(episodes) * a
    epsilon = np.linspace(0.8, 0.001,episodes)
    # initialize the agent
    learner = Agent(nstates, nactions, discount, max_reward=1)
    # perform the training
    start = [0,0]
    env, rewards = train_agent(learner, qtarget, qstart, start, mag_field,
                    dt, time_evolution, fidelity, episodes, episode_length, 
                    epsilon, alpha, verbose=5000)
    # plot result
    fname = 'train_result'+'_'+str(a)+'.png'
    fname = out_dir / fname
    plt.close('all')
    fig = plt.figure(figsize=(10,6))
    plt.scatter(range(episodes), rewards, marker = '.', alpha=0.8)
    plt.xlabel('Episode number', fontsize=14)
    plt.ylabel('Average reward', fontsize=14)
    plt.savefig(fname)
    plt.show()
    plt.close(fig=fig)



