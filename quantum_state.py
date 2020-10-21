'''
    Created on Oct 18, 2020

    @author: Alberto Chimenti

    Purpose: (PYTHON3 IMPLEMENTATION)
        Implementation of some qbit state manipulation functions
'''

### To read for further implementation:
# https://www.researchgate.net/publication/47744360_Spin_operator_matrix_elements_in_the_quantum_Ising_chain_Fermion_approach

#%%
import numpy as np
'''
    Global variable for easier use (BEWARE OF LOOP INDICES CHOICE)
'''
i = 0. + 1.j

def hamiltonian(field, single=True):
    '''
        Flexible implementation of naive ising hamiltonian
    '''
    if single:
        H=np.array([[field, 1],[1, -field]], dtype=complex)
        return(H)
    else:
        pass


def time_evolution(psi, dt, field, trotter=False):
    '''
        Flexible implementation of time evolution of pure quantum states
        for a variable number of qbits
        --> To implement other options than Trotter-Suzuki decomposition for time
            evolution unitary operator
    '''
    if trotter:
        identity = np.diag(np.ones(len(psi)))
        psi = np.dot((identity -i*hamiltonian(field)*dt), psi)
        return(psi)
    else:
        if len(psi) == 2: #this method only works for one qubit
            #implements evolution using spectral method for one qubit
            #ep_state = np.array([(1 - np.sqrt(1 + field*field))/np.sqrt(2 * (1 + field*field - np.sqrt(1 + field*field))), 
            #                    field / np.sqrt(2 * (1 + field*field - np.sqrt(1 + field*field)))], dtype=complex)
            #em_state = np.array([(1 + np.sqrt(1 + field*field))/np.sqrt(2 * (1 + field*field + np.sqrt(1 + field*field))), 
            #                    field / np.sqrt(2 * (1 + field*field + np.sqrt(1 + field*field)))], dtype=complex)

            ep_state = np.array([(1 - np.sqrt(1 + field*field))/field, 1], dtype=complex)
            em_state = np.array([(1 + np.sqrt(1 + field*field))/field, 1], dtype=complex)
            #print(ep_state, "\n", em_state)

            ep_state = ep_state/np.sqrt(np.vdot(ep_state, ep_state))
            em_state = em_state/np.sqrt(np.vdot(em_state, em_state))
            #print("----->",ep_state, "\n", em_state,"<-----\n\n")

            ep_autoval = np.sqrt(1 + field**2)
            em_autoval = -np.sqrt(1 + field**2)

            cp = np.vdot(ep_state,psi)
            cm = np.vdot(em_state,psi)

            psi= cp * np.exp(- i * ep_autoval * dt) * ep_state + cm * np.exp(- i * em_autoval * dt) * em_state
            
            return psi
        else:
            pass


def fidelity(target, psi):
    F = np.abs(np.vdot(target, psi))
    return F


if __name__ == "__main__":

    H = hamiltonian(-2)
    print(H)

    target = np.array([0. + 0.j,-1/np.sqrt(2)-1/np.sqrt(2)*i])
    psi = np.array([+1/np.sqrt(2)+1/np.sqrt(2)*i,0. + 0.j])

    print(psi)
    for h in [-4, -2, 2, 4]:
        print("Field=", h)
        print("\n")
        psi_trotter = time_evolution(psi, 0.05, h)
        psi_spectral= time_evolution(psi, 0.05, h, trotter=False)

        print("Trotter:", psi_trotter)
        print("Fidelity_trotter", fidelity(psi_trotter, psi_trotter))
        print("\n")
        print("Spectral:", psi_spectral)
        print("Fidelity_spectral", fidelity(psi_spectral, psi_spectral))
        print("\n")
        print("\n")
    print(fidelity(psi, psi))
    print(1/np.sqrt(2))
